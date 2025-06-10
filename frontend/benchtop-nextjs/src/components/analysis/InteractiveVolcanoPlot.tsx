// frontend/benchtop-nextjs/src/components/analysis/InteractiveVolcanoPlot.tsx
"use client";

import React, { useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { type Layout, type Data } from 'plotly.js';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';

// Import the centralized, strongly-typed interfaces
import { type VolcanoPlotData, type VolcanoPoint } from '@/types/analysis';

// A more precise type for our scatter plot traces
type ScatterTrace = Partial<Data> & {
    x: number[];
    y: number[];
    text: string[];
};

export default function InteractiveVolcanoPlot({ plotData }: { plotData: VolcanoPlotData }) {
    const { plot_data, default_plot_config } = plotData;

    const [title, setTitle] = useState(default_plot_config.title);
    const [fcThreshold, setFcThreshold] = useState(default_plot_config.fold_change_threshold);
    const [pValThreshold, setPValThreshold] = useState(default_plot_config.p_value_threshold);

    const { traces, layout, significantCounts } = useMemo(() => {
        const up_regulated: ScatterTrace = { x: [], y: [], text: [], type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.up || 'Upregulated', marker: { color: default_plot_config.colors.up } };
        const down_regulated: ScatterTrace = { x: [], y: [], text: [], type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.down || 'Downregulated', marker: { color: default_plot_config.colors.down } };
        const neutral: ScatterTrace = { x: [], y: [], text: [], type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.neutral || 'No Change', marker: { color: default_plot_config.colors.neutral, opacity: 0.5 } };
        
        let upCount = 0;
        let downCount = 0;

        plot_data.forEach((d: VolcanoPoint) => {
            const isUp = d._log2fc >= fcThreshold && d._pvalue < pValThreshold;
            const isDown = d._log2fc <= -fcThreshold && d._pvalue < pValThreshold;

            if (isUp) {
                up_regulated.x.push(d._log2fc);
                up_regulated.y.push(d._minus_log10_pvalue_);
                up_regulated.text.push(d._gene);
                upCount++;
            } else if (isDown) {
                down_regulated.x.push(d._log2fc);
                down_regulated.y.push(d._minus_log10_pvalue_);
                down_regulated.text.push(d._gene);
                downCount++;
            } else {
                neutral.x.push(d._log2fc);
                neutral.y.push(d._minus_log10_pvalue_);
                neutral.text.push(d._gene);
            }
        });
        
        const yMax = plot_data.length > 0 ? Math.max(...plot_data.map((d: VolcanoPoint) => d._minus_log10_pvalue_)) : 10;
        const xVals = plot_data.length > 0 ? plot_data.map((d: VolcanoPoint) => d._log2fc) : [-1, 1];
        const xRange = [Math.min(...xVals), Math.max(...xVals)];

        // Correctly typed layout object
        const plotLayout: Partial<Layout> = {
            title: { text: title },
            xaxis: { title: { text: default_plot_config.x_axis_label }, range: xRange },
            yaxis: { title: { text: default_plot_config.y_axis_label }, range: [0, yMax * 1.1] },
            shapes: [
                { type: 'line', x0: fcThreshold, x1: fcThreshold, y0: 0, y1: yMax * 1.1, line: { color: 'grey', width: 2, dash: 'dash' } },
                { type: 'line', x0: -fcThreshold, x1: -fcThreshold, y0: 0, y1: yMax * 1.1, line: { color: 'grey', width: 2, dash: 'dash' } },
                { type: 'line', x0: xRange[0], x1: xRange[1], y0: -Math.log10(pValThreshold), y1: -Math.log10(pValThreshold), line: { color: 'grey', width: 2, dash: 'dash' } }
            ],
            hovermode: 'closest',
            showlegend: true,
        };

        return { traces: [down_regulated, up_regulated, neutral], layout: plotLayout, significantCounts: { up: upCount, down: downCount } };
    }, [plot_data, title, fcThreshold, pValThreshold, default_plot_config]);

    const downloadSignificantGenes = () => {
        const significant = plot_data.filter((d: VolcanoPoint) => (d._log2fc >= fcThreshold || d._log2fc <= -fcThreshold) && d._pvalue < pValThreshold);
        const csvContent = "data:text/csv;charset=utf-8," 
            + "gene,log2_fold_change,p_value,status\n" 
            + significant.map((d: VolcanoPoint) => `${d._gene},${d._log2fc},${d._pvalue},${d._log2fc > 0 ? 'upregulated' : 'downregulated'}`).join("\n");
        
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "significant_genes.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            <div className="lg:col-span-2">
                <Card>
                    <CardContent className="p-0">
                        <Plot
                            data={traces}
                            layout={layout}
                            useResizeHandler={true}
                            className="w-full h-[600px]"
                        />
                    </CardContent>
                </Card>
            </div>
            <div className="space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Plot Controls</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label htmlFor="plot-title">Plot Title</Label>
                            <Input id="plot-title" value={title} onChange={(e) => setTitle(e.target.value)} />
                        </div>
                        <div className="grid gap-2">
                            <div className="flex justify-between items-center">
                                <Label>Log2 Fold Change Threshold</Label>
                                <span className="text-sm font-mono">{fcThreshold.toFixed(2)}</span>
                            </div>
                            <Slider defaultValue={[fcThreshold]} min={0} max={5} step={0.1} onValueChange={(value: number[]) => setFcThreshold(value[0])} />
                        </div>
                        <div className="grid gap-2">
                            <div className="flex justify-between items-center">
                                <Label>P-value Threshold</Label>
                                <span className="text-sm font-mono">{pValThreshold.toExponential(1)}</span>
                            </div>
                            <Slider defaultValue={[pValThreshold]} min={0.0001} max={0.1} step={0.001} onValueChange={(value: number[]) => setPValThreshold(value[0])} />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle>Data Extraction</CardTitle>
                        <CardDescription>Based on current thresholds.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex justify-between font-medium">
                            <span>Upregulated:</span>
                            <span className="font-mono text-green-600">{significantCounts.up}</span>
                        </div>
                        <div className="flex justify-between font-medium">
                            <span>Downregulated:</span>
                            <span className="font-mono text-blue-600">{significantCounts.down}</span>
                        </div>
                        <Button onClick={downloadSignificantGenes} className="w-full">
                            Download Significant Genes (CSV)
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}