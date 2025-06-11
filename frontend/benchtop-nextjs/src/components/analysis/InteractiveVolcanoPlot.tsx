// frontend/benchtop-nextjs/src/components/analysis/InteractiveVolcanoPlot.tsx
"use client";

import React, { useState, useMemo, useCallback } from 'react';
// Import the small, safe bundle
import Plotly from 'plotly.js-basic-dist-min';
// Import the React wrapper component
import Plot from 'react-plotly.js';
import { type Layout, type Data } from 'plotly.js';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import { Download, Palette, LineChart } from 'lucide-react';

import { type VolcanoPlotData, type VolcanoPoint } from '@/types/analysis';

type ScatterTrace = Partial<Data> & {
    x: number[];
    y: number[];
    text: string[];
};

const CustomCheckbox = ({ label, checked, onCheckedChange }: { label: string, checked: boolean, onCheckedChange: (checked: boolean) => void }) => (
    <div className="flex items-center space-x-2">
        <Checkbox id={label} checked={checked} onCheckedChange={onCheckedChange} />
        <label htmlFor={label} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            {label}
        </label>
    </div>
);

export default function InteractiveVolcanoPlot({ plotData }: { plotData: VolcanoPlotData }) {
    const { plot_data, default_plot_config } = plotData;

    const [title, setTitle] = useState(default_plot_config.title);
    const [fcThreshold, setFcThreshold] = useState(default_plot_config.fold_change_threshold);
    const [pValThreshold, setPValThreshold] = useState(default_plot_config.p_value_threshold);
    
    const [showThresholdLines, setShowThresholdLines] = useState(true);
    const [showGridLines, setShowGridLines] = useState(true);
    const [upColor, setUpColor] = useState(default_plot_config.colors.up);
    const [downColor, setDownColor] = useState(default_plot_config.colors.down);
    const [yAxisMax, setYAxisMax] = useState<number | undefined>(undefined);
    const [xAxisMax, setXAxisMax] = useState<number | undefined>(undefined);
    
    const { traces, layout, significantCounts, xRange, yMax } = useMemo(() => {
        const up_regulated: ScatterTrace = { x: [], y: [], text: [], type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.up || 'Upregulated', marker: { color: upColor } };
        const down_regulated: ScatterTrace = { x: [], y: [], text: [], type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.down || 'Downregulated', marker: { color: downColor } };
        const neutral: ScatterTrace = { x: [], y: [], text: [], type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.neutral || 'No Change', marker: { color: default_plot_config.colors.neutral, opacity: 0.5 } };
        
        plot_data.forEach((d: VolcanoPoint) => {
            const isUp = d._log2fc >= fcThreshold && d._pvalue < pValThreshold;
            const isDown = d._log2fc <= -fcThreshold && d._pvalue < pValThreshold;
            if (isUp) {
                up_regulated.x.push(d._log2fc);
                up_regulated.y.push(d._minus_log10_pvalue_);
                up_regulated.text.push(d._gene);
            } else if (isDown) {
                down_regulated.x.push(d._log2fc);
                down_regulated.y.push(d._minus_log10_pvalue_);
                down_regulated.text.push(d._gene);
            } else {
                neutral.x.push(d._log2fc);
                neutral.y.push(d._minus_log10_pvalue_);
                neutral.text.push(d._gene);
            }
        });
        
        const calculatedYMax = plot_data.length > 0 ? Math.max(...plot_data.map(d => d._minus_log10_pvalue_)) : 10;
        const xVals = plot_data.length > 0 ? plot_data.map(d => d._log2fc) : [-1, 1];
        const calculatedXAbsMax = Math.max(...xVals.map(Math.abs));

        const plotLayout: Partial<Layout> = {
            title: { text: title },
            xaxis: { 
                title: { text: default_plot_config.x_axis_label },
                range: xAxisMax ? [-xAxisMax, xAxisMax] : [-calculatedXAbsMax * 1.1, calculatedXAbsMax * 1.1],
                gridcolor: showGridLines ? '#eee' : 'rgba(0,0,0,0)',
                zerolinecolor: showGridLines ? '#eee' : 'rgba(0,0,0,0)',
            },
            yaxis: { 
                title: { text: default_plot_config.y_axis_label },
                range: [0, yAxisMax ? yAxisMax : calculatedYMax * 1.1],
                gridcolor: showGridLines ? '#eee' : 'rgba(0,0,0,0)',
                zerolinecolor: showGridLines ? '#eee' : 'rgba(0,0,0,0)',
            },
            shapes: showThresholdLines ? [
                { type: 'line', x0: fcThreshold, x1: fcThreshold, y0: 0, y1: yAxisMax || calculatedYMax * 1.1, line: { color: 'grey', width: 2, dash: 'dash' } },
                { type: 'line', x0: -fcThreshold, x1: -fcThreshold, y0: 0, y1: yAxisMax || calculatedYMax * 1.1, line: { color: 'grey', width: 2, dash: 'dash' } },
                { type: 'line', x0: -(xAxisMax || calculatedXAbsMax * 1.1), x1: (xAxisMax || calculatedXAbsMax * 1.1), y0: -Math.log10(pValThreshold), y1: -Math.log10(pValThreshold), line: { color: 'grey', width: 2, dash: 'dash' } }
            ] : [],
            hovermode: 'closest',
            showlegend: true,
            autosize: true,
        };

        return { traces: [down_regulated, up_regulated, neutral], layout: plotLayout, significantCounts: { up: up_regulated.x.length, down: down_regulated.x.length }, xRange: calculatedXAbsMax, yMax: calculatedYMax };
    }, [plot_data, title, fcThreshold, pValThreshold, default_plot_config, showThresholdLines, showGridLines, upColor, downColor, yAxisMax, xAxisMax]);

    const downloadGeneList = useCallback((filter: 'up' | 'down') => {
        const genesToDownload = plot_data.filter((d: VolcanoPoint) => {
            if (filter === 'up') return d._log2fc >= fcThreshold && d._pvalue < pValThreshold;
            if (filter === 'down') return d._log2fc <= -fcThreshold && d._pvalue < pValThreshold;
            return false;
        });
        const csvContent = "data:text/csv;charset=utf-8," 
            + "gene,log2_fold_change,p_value\n" 
            + genesToDownload.map(d => `${d._gene},${d._log2fc},${d._pvalue}`).join("\n");
        const link = document.createElement("a");
        link.setAttribute("href", encodeURI(csvContent));
        link.setAttribute("download", `${filter}_regulated_genes.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, [plot_data, fcThreshold, pValThreshold]);
    
    const downloadPlot = async () => {
        const plotContainer = document.querySelector('.plotly') as any;
        if (plotContainer && plotContainer.el) {
            const dataUrl = await Plotly.toImage(plotContainer.el, { format: 'png', width: 1200, height: 800, scale: 2 });
            const link = document.createElement('a');
            link.download = `${title.replace(/\s+/g, '_')}.png`;
            link.href = dataUrl;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            <div className="lg:col-span-2">
                <Card>
                    <CardContent className="p-0">
                        <Plot
                            data={traces as Data[]}
                            layout={layout}
                            useResizeHandler={true}
                            className="w-full h-[600px]"
                            // This is the crucial part: we tell the wrapper to use our small bundle
                            plotly={Plotly}
                            config={{
                                // Disable the Plotly logo and mode bar buttons we don't need
                                displaylogo: false,
                                modeBarButtonsToRemove: ['sendDataToCloud', 'select2d', 'lasso2d']
                            }}
                        />
                    </CardContent>
                </Card>
            </div>
            <div className="space-y-6">
                <Card>
                    <CardHeader><CardTitle>Plot Controls</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label htmlFor="plot-title">Plot Title</Label>
                            <Input id="plot-title" value={title} onChange={(e) => setTitle(e.target.value)} />
                        </div>
                        <div className="grid gap-2">
                            <Label>Fold Change Threshold</Label>
                            <Slider defaultValue={[fcThreshold]} min={0} max={Math.ceil(xRange)} step={0.1} onValueChange={(value) => setFcThreshold(value[0])} />
                        </div>
                        <div className="grid gap-2">
                            <Label>P-value Threshold</Label>
                            <Slider defaultValue={[pValThreshold]} min={0.0001} max={0.1} step={0.001} onValueChange={(value) => setPValThreshold(value[0])} />
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><Palette size={20} /> Appearance</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <CustomCheckbox label="Threshold Lines" checked={showThresholdLines} onCheckedChange={setShowThresholdLines} />
                            <CustomCheckbox label="Grid Lines" checked={showGridLines} onCheckedChange={setShowGridLines} />
                        </div>
                        <div className="grid grid-cols-3 gap-2 items-center">
                            <Label>Colors:</Label>
                            <Input type="color" value={upColor} onChange={(e) => setUpColor(e.target.value)} title="Upregulated color" />
                            <Input type="color" value={downColor} onChange={(e) => setDownColor(e.target.value)} title="Downregulated color" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-1">
                                <Label>Y-Axis Max</Label>
                                <Input type="number" placeholder={`Auto (${yMax.toFixed(1)})`} onChange={(e) => setYAxisMax(e.target.value ? parseFloat(e.target.value) : undefined)} />
                            </div>
                            <div className="grid gap-1">
                                <Label>X-Axis Max</Label>
                                <Input type="number" placeholder={`Auto (${xRange.toFixed(1)})`} onChange={(e) => setXAxisMax(e.target.value ? parseFloat(e.target.value) : undefined)} />
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><Download size={20} /> Data & Image</CardTitle></CardHeader>
                    <CardContent className="space-y-2">
                        <div className="flex justify-between font-medium"><span>Upregulated:</span><span className="font-mono text-green-600">{significantCounts.up}</span></div>
                        <div className="flex justify-between font-medium"><span>Downregulated:</span><span className="font-mono text-blue-600">{significantCounts.down}</span></div>
                        <Button onClick={() => downloadGeneList('up')} variant="outline" className="w-full">Download Upregulated Genes</Button>
                        <Button onClick={() => downloadGeneList('down')} variant="outline" className="w-full">Download Downregulated Genes</Button>
                        <Button onClick={downloadPlot} className="w-full mt-4">Download Plot as PNG</Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}