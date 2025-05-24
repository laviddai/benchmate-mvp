# backend/app/celery_worker.py
from celery import Celery
import time
import os
import uuid # For converting string ID back to UUID
from datetime import datetime # For timestamps

# Import necessary application components
# These imports happen *inside the Celery worker process*
from app.db.session import SessionLocal # To create new DB sessions in the worker
from app import crud, models, schemas   # Your CRUD, Models, Schemas
from app.models.analysis_run import AnalysisStatus # The Enum
from app.core.config import settings
from app.services import s3_service # Your S3 service

# --- (Celery app initialization - keep as is) ---
REDIS_HOSTNAME = os.getenv("REDIS_HOSTNAME", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
CELERY_BROKER_URL = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOSTNAME}:{REDIS_PORT}/1"

celery_app = Celery(
    "benchmate_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['app.celery_worker']
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
# --- (End Celery app initialization) ---


@celery_app.task(name="app.celery_worker.debug_task")
def debug_task(x: int, y: int) -> int:
    print(f"Debug task started with args: x={x}, y={y}")
    time.sleep(5)
    result = x + y
    print(f"Debug task finished. Result: {result}")
    return result


# --- MODIFIED Volcano Plot Task ---
@celery_app.task(name="app.celery_worker.run_volcano_plot_analysis", bind=True, max_retries=3, default_retry_delay=60)
def run_volcano_plot_analysis(self, analysis_run_id: str, dataset_s3_path: str, parameters: dict):
    print(f"TASK STARTED: run_volcano_plot_analysis for AnalysisRun ID: {analysis_run_id}")
    # ... (logging input dataset_s3_path and parameters - keep as is) ...

    db: Session = SessionLocal()
    analysis_run_uuid = uuid.UUID(analysis_run_id)
    db_run: Optional[models.AnalysisRun] = None
    input_file_buffer: Optional[io.BytesIO] = None # For the downloaded file

    try:
        db_run = crud.get_analysis_run(db, analysis_run_id=analysis_run_uuid)
        if not db_run:
            print(f"TASK ERROR: AnalysisRun {analysis_run_id} not found. Aborting task.")
            return {"status": "error", "message": "AnalysisRun not found, cannot proceed."}

        if db_run.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED]:
            print(f"TASK INFO: AnalysisRun {analysis_run_id} already in terminal state {db_run.status}. Skipping.")
            return {"status": db_run.status.value, "analysis_run_id": analysis_run_id, "message": "Already processed."}

        crud.update_analysis_run_status(db=db, db_run=db_run, status=AnalysisStatus.RUNNING)
        print(f"TASK INFO: AnalysisRun {analysis_run_id} status set to RUNNING.")

        # 1. Download input dataset from S3/MinIO
        print(f"TASK INFO: Attempting to download dataset from S3 path: {dataset_s3_path}")
        if not dataset_s3_path or not dataset_s3_path.startswith(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/"):
            actual_bucket_name = dataset_s3_path.split("://")[1].split("/")[0] if "://" in dataset_s3_path else "unknown"
            expected_bucket_name = settings.S3_BUCKET_NAME_DATASETS
            error_detail = (
                f"Invalid S3 path format or incorrect bucket for dataset. "
                f"Path: '{dataset_s3_path}', Expected bucket: '{expected_bucket_name}', "
                f"Actual bucket in path: '{actual_bucket_name}'."
            )
            print(f"TASK ERROR: {error_detail}")
            raise ValueError(error_detail) # This will be caught by the main except block

        s3_object_key = dataset_s3_path.replace(f"s3://{settings.S3_BUCKET_NAME_DATASETS}/", "", 1)
        print(f"TASK INFO: Extracted S3 object key: '{s3_object_key}' from bucket '{settings.S3_BUCKET_NAME_DATASETS}'")

        input_file_buffer = s3_service.download_file_to_buffer(
            bucket_name=settings.S3_BUCKET_NAME_DATASETS,
            object_key=s3_object_key
        )

        if not input_file_buffer:
            # Error already logged by s3_service.download_file_to_buffer
            raise Exception(f"Failed to download dataset '{s3_object_key}' from S3 bucket '{settings.S3_BUCKET_NAME_DATASETS}'.")
        
        print(f"TASK INFO: Dataset '{s3_object_key}' downloaded successfully into memory.")

        # 2. Dynamically import and run the volcano_processor
        from app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq import volcano_processor
        from app.utils.config_loader import load_yaml_config
        # Assuming your volcano processor expects Pydantic schema for params
        from app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.volcano import VolcanoParams as ToolVolcanoParams

        tool_config_yaml_path = "benchtop/biology/omics/transcriptomics/bulk_rna_seq/volcano.yaml"
        tool_default_config = load_yaml_config(tool_config_yaml_path)
        
        # Ensure parameters received by the task are correctly structured for ToolVolcanoParams
        # The API endpoint should have prepared these.
        processor_params_obj = ToolVolcanoParams(**parameters)

        print(f"TASK INFO: Running volcano_processor with params: {processor_params_obj.model_dump()}")
        
        # The volcano_processor.run function needs to accept a file-like object (the buffer)
        # and the Pydantic params object, and the config dict.
        # Ensure volcano_processor.run is adapted for this.
        # Specifically, it uses load_data which expects a file_obj and an extension.
        # We need to provide an extension. Let's try to infer it from the original s3_object_key.
        file_extension = os.path.splitext(s3_object_key)[1].lower()
        if not file_extension: # Fallback if no extension in key
            file_extension = ".csv" # Or determine from dataset metadata if available
            print(f"TASK WARNING: No extension in S3 key, defaulting to '{file_extension}' for processor.")

        # The load_data in volcano_processor expects file_obj.file if it's an UploadFile.
        # For BytesIO, we pass it directly.
        # We need to ensure volcano_processor.load_data can handle BytesIO.
        # Current volcano_processor.load_data:
        #   def load_data(file_obj, ext):
        #       if ext in ['.xls', '.xlsx']: return pd.read_excel(file_obj)
        #       else: return pd.read_csv(file_obj)
        # This should work fine with input_file_buffer as it's a file-like object.

        result_dict = volcano_processor.run(
            file_obj=input_file_buffer, # Pass the BytesIO buffer
            params=processor_params_obj,
            config=tool_default_config,
            # Pass the extension explicitly if your run function needs it for load_data
            # Or modify run to pass it to load_data.
            # For now, let's assume run passes it or load_data is adapted.
            # If volcano_processor.run itself calls load_data, it needs the ext.
            # Let's modify volcano_processor.run slightly later or pass ext.
            # For now, we'll assume it can get the ext or is adapted.
            # The `run` function in your XML for volcano_processor.py already does:
            #   ext = getattr(file_obj, "filename", "").split(".")[-1]
            #   df = load_data(file_obj.file if hasattr(file_obj, "file") else file_obj, f".{ext}")
            # This won't work directly with BytesIO as it doesn't have 'filename'.
            # We need to pass the buffer and the extension to the run function.
            # Let's assume we modify volcano_processor.run to accept `file_buffer` and `file_ext`
        )
        # For now, let's simulate the direct call to load_data and plot_volcano
        # as if the processor was inlined here, to test the buffer.
        # df = volcano_processor.load_data(input_file_buffer, file_extension)
        # mapping_for_plot = { # Construct this from processor_params_obj
        #    "pvalue": processor_params_obj.pvalue_col or tool_default_config["expected_columns"]["pvalue"],
        #    "log2fc": processor_params_obj.log2fc_col or tool_default_config["expected_columns"]["log2fc"],
        #    "gene": processor_params_obj.gene_col or tool_default_config["expected_columns"]["gene"]
        # }
        # df_proc = volcano_processor.preprocess_data(df.copy(), mapping=mapping_for_plot)
        # fig = volcano_processor.plot_volcano(
        #     df=df_proc,
        #     # ... other plot params from processor_params_obj and tool_default_config ...
        #     x_col=mapping_for_plot["log2fc"],
        #     y_col=mapping_for_plot["pvalue"],
        #     gene_col=mapping_for_plot["gene"],
        #     fc_thresh=processor_params_obj.fold_change_threshold,
        #     pval_thresh=processor_params_obj.p_value_threshold
        # )
        # plot_base64 = volcano_processor.fig_to_base64(fig)
        # result_dict = {"plot_image": plot_base64, "summary": {"genes_analyzed": len(df_proc)}}
        # print(f"TASK INFO: Volcano plot processing complete. Genes analyzed: {result_dict['summary']['genes_analyzed']}")

        # For now, we will assume result_dict is correctly populated by volcano_processor.run
        # The volcano_processor.run in your XML needs to be adapted to take the buffer and ext.
        # Let's assume it is for now.
        # If volcano_processor.run expects a filename for ext extraction, we need to pass it.
        # The `run` function in your XML:
        # `def run(file_obj, params: VolcanoParams, config: dict) -> dict:`
        # `ext = getattr(file_obj, "filename", "").split(".")[-1]`
        # This needs to change. It should take `file_buffer` and `file_extension`
        # Or, the `run` function itself should be more intelligent.

        # Let's make a small adaptation to how we call the processor's run function
        # by creating a mock file_obj with a name for the processor.
        class MockFileWithFilename:
            def __init__(self, buffer, filename):
                self.file = buffer
                self.filename = filename
        
        mock_file_obj = MockFileWithFilename(input_file_buffer, s3_object_key.split('/')[-1])

        result_dict = volcano_processor.run(
            file_obj=mock_file_obj, # Pass the mock file object
            params=processor_params_obj,
            config=tool_default_config
        )
        print(f"TASK INFO: Volcano plot processing complete. Summary: {result_dict.get('summary')}")


        # 3. Upload output plot to S3/MinIO
        plot_base64 = result_dict.get("plot_image")
        if not plot_base64 or not plot_base64.startswith("data:image/png;base64,"):
            raise ValueError("Processor did not return a valid base64 PNG plot image.")

        import base64
        image_data_base64 = plot_base64.split(",")[1]
        image_bytes = base64.b64decode(image_data_base64)
        plot_image_buffer = io.BytesIO(image_bytes)

        plot_s3_object_name = f"analysis_runs/{analysis_run_id}/results/volcano_plot.png"
        
        # Use a synchronous upload method for the plot buffer
        # We need to adapt s3_service or use s3_client directly for this.
        # Let's add a simple sync upload for BytesIO to s3_service.
        # For now, using the existing s3_service.s3_client.upload_fileobj directly
        s3_service.s3_client.upload_fileobj(
            plot_image_buffer,
            settings.S3_BUCKET_NAME_RESULTS,
            plot_s3_object_name
        )
        print(f"TASK INFO: Plot image uploaded to S3: s3://{settings.S3_BUCKET_NAME_RESULTS}/{plot_s3_object_name}")

        output_artifacts = {
            "plot_image_s3_path": f"s3://{settings.S3_BUCKET_NAME_RESULTS}/{plot_s3_object_name}",
            "summary_stats": result_dict.get("summary", {}),
        }
        final_status = AnalysisStatus.COMPLETED
        final_error_message = None
        final_run_log_update = "\nVolcano plot analysis completed successfully."

    except Exception as e:
        # ... (existing error handling) ...
        print(f"TASK ERROR: Exception during volcano plot for {analysis_run_id}: {str(e)}")
        import traceback
        final_run_log_update = f"\nVolcano plot analysis FAILED: {str(e)}\n{traceback.format_exc()}"
        final_status = AnalysisStatus.FAILED
        final_error_message = str(e)
        output_artifacts = {"error_details": traceback.format_exc()}


    finally:
        if db_run:
            print(f"TASK INFO: Updating final status for {analysis_run_id} to {final_status.value}")
            crud.update_analysis_run_status(
                db=db,
                db_run=db_run,
                status=final_status,
                error_message=final_error_message,
                run_log_update=final_run_log_update
            )
            if final_status == AnalysisStatus.COMPLETED:
                crud.update_analysis_run_outputs(db=db, db_run=db_run, output_artifacts=output_artifacts)
        if input_file_buffer: # Close the buffer if it was opened
            input_file_buffer.close()
        db.close()

    return {"status": final_status.value, "analysis_run_id": analysis_run_id, "outputs": output_artifacts}