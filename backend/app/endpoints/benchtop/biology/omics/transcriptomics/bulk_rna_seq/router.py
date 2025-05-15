import importlib
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from backend.app.utils.config_loader import load_yaml_config
from backend.app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.tool_base import ToolParams, ToolResponse

router = APIRouter()
base_cfg_dir = Path(__file__).resolve().parent.parent.parent.parent / 'config' / 'benchtop' / 'biology' / 'omics' / 'transcriptomics' / 'bulk_rna_seq'

@router.get('/tools', summary='List available bulk-RNA-seq tools')
def list_tools():
    return [p.stem for p in base_cfg_dir.glob('*.yaml')]

@router.post('/{tool}/run', response_model=ToolResponse, summary='Run selected bulk-RNA-seq tool')
async def run_tool(
    tool: str,
    file: UploadFile = File(...),
    params: ToolParams = Depends()
):
    # 1) Validate tool
    yaml_rel = f'benchtop/biology/omics/transcriptomics/bulk_rna_seq/{tool}.yaml'
    try:
        config = load_yaml_config(yaml_rel)
    except RuntimeError:
        raise HTTPException(404, f"Tool not found: {tool}")

    # 2) Load schema and revalidate tool-specific params
    schema_mod = importlib.import_module(f'backend.app.schemas.benchtop.biology.omics.transcriptomics.bulk_rna_seq.{tool}')
    ToolSpecificParams = getattr(schema_mod, f'{tool.capitalize()}Params')
    tool_params = ToolSpecificParams(**params.dict(exclude_none=True))

    # 3) Load and run processor
    proc_mod = importlib.import_module(
        f'backend.app.utils.benchtop.biology.omics.transcriptomics.bulk_rna_seq.{tool}_processor'
    )
    try:
        result = proc_mod.run(file.file, tool_params, config)
    except Exception as e:
        raise HTTPException(500, str(e))

    return result