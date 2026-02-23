import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Bot, Repeat, Scale } from 'lucide-react';

export function ConditionNode({ data }: NodeProps) {
    const isRunning = data.isRunning as boolean;
    const payload = data.payload as any;

    return (
        <div className={`bg-white border-2 ${isRunning ? 'border-yellow-400 shadow-yellow-200 shadow-lg' : 'border-indigo-200'} rounded-lg shadow-sm min-w-[200px] overflow-hidden transition-all duration-300`}>
            <div className="bg-indigo-50 px-3 py-2 border-b border-indigo-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Scale className={`w-4 h-4 ${isRunning ? 'text-yellow-500 animate-pulse' : 'text-indigo-500'}`} />
                    <span className="font-semibold text-sm text-indigo-900">{String(data.label || 'Condition')}</span>
                </div>
            </div>
            <div className="px-3 py-3 text-xs text-slate-500 bg-slate-50 flex flex-col gap-2">
                <span>Evaluates and branches based on logic</span>
                {payload && (
                    <div className="mt-2 bg-slate-900 text-green-400 p-2 rounded text-[10px] font-mono overflow-auto max-w-full max-h-32">
                        {JSON.stringify(payload, null, 2)}
                    </div>
                )}
            </div>

            {/* Default Input Handle */}
            <Handle type="target" position={Position.Top} className="w-3 h-3 bg-indigo-400" />

            {/* Explicit True/False Branching Output Handles */}
            <Handle
                type="source"
                position={Position.Bottom}
                id="true"
                className="w-3 h-3 bg-green-500"
                style={{ left: '30%' }}
            />
            <div className="absolute text-[10px] font-bold text-green-600" style={{ bottom: -20, left: '20%' }}>TRUE</div>

            <Handle
                type="source"
                position={Position.Bottom}
                id="false"
                className="w-3 h-3 bg-red-500"
                style={{ left: '70%' }}
            />
            <div className="absolute text-[10px] font-bold text-red-600" style={{ bottom: -20, left: '60%' }}>FALSE</div>
        </div>
    );
}

// Simple stylistic LLM/Agent node to replace the 'default' string
export function StandardNode({ data }: NodeProps) {
    const isRunning = data.isRunning as boolean;
    const payload = data.payload as any;

    return (
        <div className={`bg-white border-2 ${isRunning ? 'border-yellow-400 shadow-yellow-200 shadow-lg' : 'border-slate-200'} rounded-lg shadow-sm min-w-[200px] overflow-hidden transition-all duration-300`}>
            <div className="bg-slate-50 px-3 py-2 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Bot className={`w-4 h-4 ${isRunning ? 'text-yellow-500 animate-bounce' : 'text-slate-500'}`} />
                    <span className="font-semibold text-sm text-slate-900">{String(data.label || 'Node')}</span>
                </div>
            </div>
            {payload && (
                <div className="px-3 py-2 bg-slate-50 border-t border-slate-100">
                    <div className="bg-slate-900 text-green-400 p-2 rounded text-[10px] font-mono overflow-auto max-w-full max-h-48">
                        {JSON.stringify(payload, null, 2)}
                    </div>
                </div>
            )}
            <Handle type="target" position={Position.Top} className="w-3 h-3 bg-slate-400" />
            <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-slate-400" />
        </div>
    );
}

export function LoopNode({ data }: NodeProps) {
    return (
        <div className="bg-white border-2 border-dashed border-orange-300 rounded-xl shadow-sm overflow-hidden" style={{ minWidth: 400, minHeight: 300 }}>
            <div className="bg-orange-50 px-3 py-2 border-b border-orange-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Repeat className="w-4 h-4 text-orange-600" />
                    <span className="font-semibold text-sm text-orange-900">{String(data.label || 'Loop Container')}</span>
                </div>
                <div className="text-xs text-orange-700 bg-orange-100 px-2 py-0.5 rounded-full font-medium">
                    Iterative Group
                </div>
            </div>

            <Handle type="target" position={Position.Top} className="w-3 h-3 bg-orange-400" />
            <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-orange-400" />
        </div>
    );
}
