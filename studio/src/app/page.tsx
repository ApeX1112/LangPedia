'use client';

import React, { useState, useCallback, useEffect } from 'react';
import WorkflowCanvas from '@/components/WorkflowCanvas';
import { Layout, Save, Play, RefreshCw, Activity, Database, Plus } from 'lucide-react';
import axios from 'axios';
import { useNodesState, useEdgesState, addEdge, Connection, Edge, Node } from '@xyflow/react';

interface WorkflowNodeSpec {
  id: string;
  type: string;
  inputs?: string[];
  params?: Record<string, unknown>;
  parent?: string;
}

interface WorkflowEdgeSpec {
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
}

interface WorkflowSpec {
  name: string;
  version: string;
  nodes: WorkflowNodeSpec[];
  edges: WorkflowEdgeSpec[];
}

interface WorkflowItem {
  id: string;
  name: string;
  spec: WorkflowSpec;
  source: string;
}

const API_BASE = 'http://localhost:8000';

export default function Home() {
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const loadWorkflow = useCallback((wf: WorkflowItem) => {
    setActiveWorkflowId(wf.id);
    const spec = wf.spec;
    const newNodes: Node[] = spec.nodes.map((n: WorkflowNodeSpec, i: number) => {
      const isLoop = n.type === 'loop';
      const isCondition = n.type === 'condition';
      const isChild = !!n.parent;

      let typeStr = 'default';
      if (isLoop) typeStr = 'loop';
      if (isCondition) typeStr = 'condition';

      return {
        id: n.id,
        // Calculate dynamic relative or absolute positions
        position: isChild ? { x: 20, y: 50 + (i * 80) } : { x: 100, y: 100 + (i * 150) },
        data: { label: `${n.id} (${n.type})` },
        type: typeStr,
        parentId: n.parent, // Assign parent ID for React Flow container groups
        extent: isChild ? 'parent' : undefined, // Keep child inside parent visually
      };
    });
    setNodes(newNodes);

    const newEdges: Edge[] = spec.edges.map((e: WorkflowEdgeSpec) => ({
      id: `e-${e.source}-${e.target}-${e.sourceHandle || ''}`,
      source: e.source,
      target: e.target,
      sourceHandle: e.sourceHandle,
      label: e.label || (e.sourceHandle ? e.sourceHandle.toUpperCase() : undefined),
      animated: true,
      style: { stroke: e.sourceHandle === 'true' ? '#22c55e' : e.sourceHandle === 'false' ? '#ef4444' : '#94a3b8', strokeWidth: 2 }
    }));
    setEdges(newEdges);
  }, [setNodes, setEdges]);

  useEffect(() => {
    const initWorkflows = async () => {
      try {
        const res = await axios.get(`${API_BASE}/workflows/`);
        setWorkflows(res.data);
        if (res.data.length > 0) {
          loadWorkflow(res.data[0]);
        }
      } catch (err) {
        console.error("Failed to fetch workflows", err);
      }
    };
    initWorkflows();
  }, [loadWorkflow]);

  const fetchWorkflows = async () => {
    try {
      const res = await axios.get(`${API_BASE}/workflows/`);
      setWorkflows(res.data);
    } catch (err) {
      console.error("Failed to fetch workflows", err);
    }
  };

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds: Edge[]) => addEdge(params, eds)),
    [setEdges],
  );

  const saveWorkflow = async () => {
    const spec = {
      name: "Updated Workflow",
      version: "0.1",
      nodes: nodes.map((n: Node) => ({ id: n.id, type: 'llm', params: {} })), // Simplified mapping
      edges: edges.map((e: Edge) => ({ source: e.source, target: e.target }))
    };
    try {
      await axios.post(`${API_BASE}/workflows/`, spec);
      fetchWorkflows();
      alert("Workflow saved to backend!");
    } catch {
      alert("Save failed. Make sure backend is running.");
    }
  };

  const [runningNodeId, setRunningNodeId] = useState<string | null>(null);
  const [nodePayloads, setNodePayloads] = useState<Record<string, unknown>>({});
  const [isExecuting, setIsExecuting] = useState(false);

  // When node payloads or running status changes, we need to update our React Flow `nodes` array 
  // so the CustomNodes can consume this data via their `data` prop.
  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: {
          ...n.data,
          isRunning: n.id === runningNodeId,
          payload: nodePayloads[n.id] || null
        }
      }))
    );
  }, [runningNodeId, nodePayloads, setNodes]);

  const runWorkflow = async () => {
    if (!activeWorkflowId) return;
    setIsExecuting(true);
    setRunningNodeId(null);
    setNodePayloads({});

    try {
      const response = await fetch(`${API_BASE}/runs/stream?workflow_id=${activeWorkflowId}`, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream'
        }
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process SSE delineated by double newlines
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // keep the last incomplete chunk

        for (const event of events) {
          if (event.startsWith('data: ')) {
            const jsonStr = event.slice(6); // remove 'data: '
            try {
              const payload = JSON.parse(jsonStr);
              const { type, data } = payload;
              console.log("Stream event:", type, data);

              if (type === 'node_start') {
                setRunningNodeId(data.node_id);
              } else if (type === 'node_complete' || type === 'node_error') {
                setRunningNodeId(null);
              } else if (type === 'node_visualize') {
                setNodePayloads(prev => ({
                  ...prev,
                  [data.node_id]: data.payload
                }));
              } else if (type === 'workflow_end' || type === 'workflow_error') {
                setIsExecuting(false);
                setRunningNodeId(null);
                alert(`Execution complete. Time: ${data.elapsed?.toFixed(2) || '0'}s`);
                return; // end stream reading
              }
            } catch (e) {
              console.error("Parse error on stream chunk", e, jsonStr);
            }
          }
        }
      }
    } catch (err) {
      console.error("Stream failed:", err);
      setIsExecuting(false);
      setRunningNodeId(null);
    }
  };

  return (
    <main className="flex min-h-screen flex-col p-8 bg-white text-slate-900">
      <header className="flex justify-between items-center mb-8 border-b pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-3">
            <Layout className="text-indigo-600" /> Langpedia Studio
          </h1>
          <p className="text-slate-500">v0.1 • Connected to {API_BASE}</p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={saveWorkflow}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-md hover:bg-slate-50 transition-colors cursor-pointer text-slate-700 shadow-sm"
          >
            <Save className="w-4 h-4" /> Save
          </button>
          <button
            onClick={runWorkflow}
            disabled={isExecuting}
            className={`flex items-center gap-2 px-4 py-2 ${isExecuting ? 'bg-slate-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 active:scale-95'} text-white rounded-md transition-colors shadow-lg`}
          >
            {isExecuting ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {isExecuting ? 'Running...' : 'Run'}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-8 flex-1 overflow-hidden">
        <aside className="col-span-3 border-r pr-8 overflow-y-auto">
          <section className="mb-8">
            <h2 className="text-xs font-semibold mb-4 uppercase text-slate-400 tracking-wider">Active Workflows</h2>
            <div className="space-y-1">
              {workflows.map((wf: WorkflowItem) => (
                <button
                  key={wf.id}
                  onClick={() => loadWorkflow(wf)}
                  className={`w-full text-left p-3 rounded-md transition-all ${activeWorkflowId === wf.id ? 'bg-indigo-50 border-l-4 border-indigo-600 font-medium' : 'hover:bg-slate-50'}`}
                >
                  {wf.name}
                </button>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-xs font-semibold mb-4 uppercase text-slate-400 tracking-wider">Node Library</h2>
            <div className="space-y-2">
              {[
                { name: 'LLM Node', icon: Activity },
                { name: 'RAG Retriever', icon: Database },
                { name: 'Tool Call', icon: Plus },
              ].map((item) => (
                <div
                  key={item.name}
                  className="p-3 border rounded-md bg-white hover:border-indigo-400 cursor-grab active:cursor-grabbing flex items-center gap-3 text-slate-700 shadow-sm transition-all"
                >
                  <item.icon className="w-4 h-4 text-slate-400" /> {item.name}
                </div>
              ))}
            </div>
          </section>
        </aside>

        <section className="col-span-9 h-full relative">
          <WorkflowCanvas
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
          />
        </section>
      </div>
    </main>
  );
}
