'use client';

import React, { useMemo } from 'react';
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
import { ConditionNode, StandardNode, LoopNode } from './CustomNodes';

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
    const nodeTypes = useMemo(() => ({
        condition: ConditionNode,
        loop: LoopNode,
        default: StandardNode,
        input: StandardNode // Replace with specific input later if needed
    }), []);

    return (
        <div style={{ width: '100%', height: '80vh' }} className="border rounded-lg bg-slate-50">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                fitView
            >
                <Background />
                <Controls />
            </ReactFlow>
        </div>
    );
}
