// frontend/benchtop-nextjs/src/components/analysis/InteractiveVolcanoPlot.tsx
"use client";

import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import Plotly from 'plotly.js-basic-dist-min';
import { type Layout, type Data, type Annotations } from 'plotly.js';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Download, Palette, Info, RotateCcw } from 'lucide-react';

import { type VolcanoPlotData, type VolcanoPoint } from '@/types/volcano.types';

interface PlotState {
    title: string;
    fcThreshold: number;
    pValThreshold: number;
    showThresholdLines: boolean;
    showGridLines: boolean;
    upColor: string;
    downColor: string;
    yAxisMax: number | null;
    xAxisMax: number | null;
    topNUp: number;
    topNDown: number;
    showPlotBorder: boolean; // 1. ADDED: New state property for the border
}

const CustomCheckbox = ({ label, checked, onCheckedChange }: { label: string, checked: boolean, onCheckedChange: (checked: boolean) => void }) => (
    <div className="flex items-center space-x-2">
        <Checkbox id={label} checked={checked} onCheckedChange={onCheckedChange} />
        <label htmlFor={label} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">{label}</label>
    </div>
);

const InfoTooltip = ({ content }: { content: string }) => (
    <TooltipProvider delayDuration={100}>
        <Tooltip>
            <TooltipTrigger asChild><button type="button" className="ml-1.5"><Info size={14} className="text-muted-foreground" /></button></TooltipTrigger>
            <TooltipContent><p className="max-w-xs">{content}</p></TooltipContent>
        </Tooltip>
    </TooltipProvider>
);

export default function InteractiveVolcanoPlot({ plotData }: { plotData: VolcanoPlotData }) {
    const plotRef = useRef<HTMLDivElement>(null);
    const { plot_data, default_plot_config } = plotData;

    const getInitialState = useCallback((): PlotState => ({
        title: default_plot_config.title,
        fcThreshold: default_plot_config.fold_change_threshold,
        pValThreshold: default_plot_config.p_value_threshold,
        showThresholdLines: true,
        showGridLines: true,
        upColor: default_plot_config.colors.up,
        downColor: default_plot_config.colors.down,
        yAxisMax: null,
        xAxisMax: null,
        topNUp: 0,
        topNDown: 0,
        showPlotBorder: false, // 1. ADDED: Initial state set to false
    }), [default_plot_config]);

    const [state, setState] = useState<PlotState>(getInitialState);

    const handleStateChange = <K extends keyof PlotState>(key: K, value: PlotState[K]) => {
        setState(prevState => ({ ...prevState, [key]: value }));
    };

    const { traces, layout, significantCounts } = useMemo(() => {
        const up = { x: [] as number[], y: [] as number[], text: [] as string[] };
        const down = { x: [] as number[], y: [] as number[], text: [] as string[] };
        const neutral = { x: [] as number[], y: [] as number[], text: [] as string[] };

        plot_data.forEach((d: VolcanoPoint) => {
            const isUp = d._log2fc >= state.fcThreshold && d._pvalue < state.pValThreshold;
            const isDown = d._log2fc <= -state.fcThreshold && d._pvalue < state.pValThreshold;
            if (isUp) {
                up.x.push(d._log2fc); up.y.push(d._minus_log10_pvalue_); up.text.push(d._gene);
            } else if (isDown) {
                down.x.push(d._log2fc); down.y.push(d._minus_log10_pvalue_); down.text.push(d._gene);
            } else {
                neutral.x.push(d._log2fc); neutral.y.push(d._minus_log10_pvalue_); neutral.text.push(d._gene);
            }
        });
        
        const allTraces: Partial<Data>[] = [
            { ...down, type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.down || 'Downregulated', marker: { color: state.downColor } },
            { ...up, type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.up || 'Upregulated', marker: { color: state.upColor } },
            { ...neutral, type: 'scatter', mode: 'markers', name: default_plot_config.legend_labels.neutral || 'No Change', marker: { color: default_plot_config.colors.neutral, opacity: 0.5 } }
        ];

        const yDataPoints = plot_data.map(d => d._minus_log10_pvalue_).filter(y => isFinite(y));
        const xDataPoints = plot_data.map(d => d._log2fc).filter(x => isFinite(x));
        const calculatedYMax = yDataPoints.length > 0 ? Math.max(...yDataPoints) : 10;
        const calculatedXAbsMax = xDataPoints.length > 0 ? Math.max(...xDataPoints.map(Math.abs)) : 5;
        
        const finalYMax = state.yAxisMax ?? calculatedYMax * 1.1;
        const finalXAbsMax = state.xAxisMax ?? calculatedXAbsMax * 1.1;

        const plotLayout: Partial<Layout> = {
            title: { text: state.title, x: 0.45, xanchor: 'center', yanchor: 'top', y: 0.95 },
            // 3. ADDED: Properties to control the border based on state
            xaxis: { 
                title: { text: default_plot_config.x_axis_label }, 
                range: [-finalXAbsMax, finalXAbsMax], 
                gridcolor: state.showGridLines ? '#eee' : 'rgba(0,0,0,0)', 
                zerolinecolor: state.showGridLines ? '#eee' : 'rgba(0,0,0,0)', 
                automargin: true,
                showline: state.showPlotBorder,
                mirror: state.showPlotBorder,
                linecolor: 'black',
                linewidth: 1,
            },
            yaxis: { 
                title: { text: default_plot_config.y_axis_label }, 
                range: [0, finalYMax], 
                gridcolor: state.showGridLines ? '#eee' : 'rgba(0,0,0,0)', 
                zerolinecolor: state.showGridLines ? '#eee' : 'rgba(0,0,0,0)', 
                automargin: true,
                showline: state.showPlotBorder,
                mirror: state.showPlotBorder,
                linecolor: 'black',
                linewidth: 1,
            },
            shapes: state.showThresholdLines ? [
                { type: 'line', x0: state.fcThreshold, x1: state.fcThreshold, y0: 0, y1: finalYMax, line: { color: 'grey', width: 2, dash: 'dash' } },
                { type: 'line', x0: -state.fcThreshold, x1: -state.fcThreshold, y0: 0, y1: finalYMax, line: { color: 'grey', width: 2, dash: 'dash' } },
                { type: 'line', x0: -finalXAbsMax, x1: finalXAbsMax, y0: -Math.log10(state.pValThreshold), y1: -Math.log10(state.pValThreshold), line: { color: 'grey', width: 2, dash: 'dash' } }
            ] : [],
            annotations: [],
            hovermode: 'closest',
            showlegend: true,
            autosize: true,
            margin: { l: 60, r: 30, t: 80, b: 60 },
        };
        
        const genesToLabel = new Set<string>();
        const addTopGenes = (data: {x: number[], y: number[], text: string[]}, n: number) => {
            const geneData = data.x.map((x, i) => ({ x, y: data.y[i], gene: data.text[i], score: Math.abs(x) * data.y[i] }));
            geneData.sort((a, b) => b.score - a.score);
            geneData.slice(0, n).forEach(item => genesToLabel.add(item.gene));
        };
        if (state.topNUp > 0) addTopGenes(up, state.topNUp);
        if (state.topNDown > 0) addTopGenes(down, state.topNDown);

        if (genesToLabel.size > 0 && plotLayout.annotations) {
            const annotations: Partial<Annotations>[] = [];
            plot_data.forEach(d => {
                if (genesToLabel.has(d._gene)) {
                    annotations.push({
                        x: d._log2fc, y: d._minus_log10_pvalue_, text: d._gene, showarrow: true, arrowhead: 0, ax: 0, ay: -25, font: { size: 10 }
                    });
                }
            });
            plotLayout.annotations = annotations;
        }

        return { traces: allTraces, layout: plotLayout, significantCounts: { up: up.x.length, down: down.x.length } };
    }, [state, plot_data, default_plot_config]);

    useEffect(() => {
        if (plotRef.current) {
            Plotly.react(plotRef.current, traces as Data[], layout, { responsive: true, displaylogo: false });
        }
    }, [traces, layout]);

    const downloadPlot = useCallback(async () => {
        if (plotRef.current) {
            const dataUrl = await Plotly.toImage(plotRef.current, { format: 'png', width: 1200, height: 800, scale: 2 });
            const link = document.createElement('a');
            link.download = `${state.title.replace(/\s+/g, '_')}.png`;
            link.href = dataUrl;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }, [state.title]);
    
    const downloadGeneList = useCallback((filter: 'up' | 'down') => {
        const genesToDownload = plot_data.filter((d: VolcanoPoint) => {
            if (filter === 'up') return d._log2fc >= state.fcThreshold && d._pvalue < state.pValThreshold;
            if (filter === 'down') return d._log2fc <= -state.fcThreshold && d._pvalue < state.pValThreshold;
            return false;
        });
        const csvContent = "data:text/csv;charset=utf-8," + "gene,log2_fold_change,p_value\n" + genesToDownload.map(d => `${d._gene},${d._log2fc},${d._pvalue}`).join("\n");
        const link = document.createElement("a");
        link.setAttribute("href", encodeURI(csvContent));
        link.setAttribute("download", `${filter}_regulated_genes.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }, [plot_data, state.fcThreshold, state.pValThreshold]);

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            <div className="lg:col-span-2 flex justify-center items-start">
                <div className="w-full" style={{ maxWidth: '800px' }}>
                    <Card>
                        <CardContent className="p-2">
                            <div ref={plotRef} className="w-full" style={{aspectRatio: '1.5 / 1'}}></div>
                        </CardContent>
                    </Card>
                </div>
            </div>
            <div className="space-y-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <CardTitle>Plot Controls</CardTitle>
                        <Button variant="ghost" size="sm" onClick={() => setState(getInitialState())}><RotateCcw size={14} className="mr-2"/>Reset</Button>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <Label htmlFor="plot-title">Plot Title</Label>
                            <Input id="plot-title" value={state.title} onChange={(e) => handleStateChange('title', e.target.value)} />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="fc-threshold-input">Fold Change Threshold</Label>
                            <Input id="fc-threshold-input" type="number" value={state.fcThreshold} onChange={(e) => handleStateChange('fcThreshold', parseFloat(e.target.value) || 0)} step={0.1} />
                        </div>
                        <div className="grid gap-2">
                            <div className="flex items-center">
                                <Label htmlFor="pval-threshold-input">P-value Threshold</Label>
                                <InfoTooltip content={`The line on the plot is drawn at -log10(${state.pValThreshold.toExponential(1)}) ≈ ${(-Math.log10(state.pValThreshold)).toFixed(2)}`} />
                            </div>
                            <Input id="pval-threshold-input" type="number" value={state.pValThreshold} onChange={(e) => handleStateChange('pValThreshold', parseFloat(e.target.value) || 0)} step={0.001} max={1} min={0}/>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><Palette size={20} /> Appearance</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <CustomCheckbox label="Threshold Lines" checked={state.showThresholdLines} onCheckedChange={(c: boolean) => handleStateChange('showThresholdLines', c)} />
                            <CustomCheckbox label="Grid Lines" checked={state.showGridLines} onCheckedChange={(c: boolean) => handleStateChange('showGridLines', c)} />
                            {/* 2. ADDED: The UI checkbox for the border */}
                            <CustomCheckbox label="Plot Border" checked={state.showPlotBorder} onCheckedChange={(c: boolean) => handleStateChange('showPlotBorder', c)} />
                        </div>
                        <div className="grid grid-cols-3 gap-2 items-center">
                            <Label>Colors:</Label>
                            <Input type="color" value={state.upColor} onChange={(e) => handleStateChange('upColor', e.target.value)} title="Upregulated color" />
                            <Input type="color" value={state.downColor} onChange={(e) => handleStateChange('downColor', e.target.value)} title="Downregulated color" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-1"><Label>Y-Axis Max</Label><Input type="number" value={state.yAxisMax ?? ''} placeholder="Auto" onChange={(e) => handleStateChange('yAxisMax', e.target.value ? parseFloat(e.target.value) : null)} /></div>
                            <div className="grid gap-1"><Label>X-Axis Max</Label><Input type="number" value={state.xAxisMax ?? ''} placeholder="Auto" onChange={(e) => handleStateChange('xAxisMax', e.target.value ? parseFloat(e.target.value) : null)} /></div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader><CardTitle className="flex items-center gap-2"><Download size={20} /> Data & Image</CardTitle></CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <div className="flex items-center">
                                <Label>Label Top Genes</Label><InfoTooltip content="Automatically label the most significant genes, calculated by |log2FC| * -log10(p-value)." />
                            </div>
                            <div className="grid grid-cols-2 gap-4 mt-1">
                                <Input type="number" placeholder="Up" min={0} step={1} value={state.topNUp || ''} onInput={(e) => handleStateChange('topNUp', parseInt(e.currentTarget.value) || 0)} />
                                <Input type="number" placeholder="Down" min={0} step={1} value={state.topNDown || ''} onInput={(e) => handleStateChange('topNDown', parseInt(e.currentTarget.value) || 0)} />
                            </div>
                        </div>
                        <div className="space-y-2 pt-2">
                             <div className="flex justify-between font-medium text-sm"><span>Upregulated:</span><span className="font-mono text-green-600">{significantCounts.up}</span></div>
                             <div className="flex justify-between font-medium text-sm"><span>Downregulated:</span><span className="font-mono text-blue-600">{significantCounts.down}</span></div>
                             <Button onClick={() => downloadGeneList('up')} variant="outline" className="w-full">Download Upregulated List</Button>
                             <Button onClick={() => downloadGeneList('down')} variant="outline" className="w-full">Download Downregulated List</Button>
                             <Button onClick={downloadPlot} className="w-full">Download Plot as PNG</Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}