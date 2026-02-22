'use client';

import React from 'react';
import {
    ReactFlow,
    Connection,
    Edge,
    Node,
    OnNodesChange,
    OnEdgesChange,
    Background,
    Controls,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface WorkflowCanvasProps {
    nodes: Node[];
    edges: Edge[];
    onNodesChange: OnNodesChange<Node>;
    onEdgesChange: OnEdgesChange<Edge>;
    onConnect: (params: Connection | Edge) => void;
}

export default function WorkflowCanvas({
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect
}: WorkflowCanvasProps) {
    return (
        <div style={{ width: '100%', height: '80vh' }} className="border rounded-lg bg-slate-50">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
}
