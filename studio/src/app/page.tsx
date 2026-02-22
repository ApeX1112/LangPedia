'use client';

import React, { useState, useCallback, useEffect } from 'react';
import WorkflowCanvas from '@/components/WorkflowCanvas';
import { Play, Save, Plus, Database, Activity, Layout } from 'lucide-react';
import axios from 'axios';
import { useNodesState, useEdgesState, addEdge, Connection, Edge, Node } from '@xyflow/react';

interface WorkflowNodeSpec {
  id: string;
  type: string;
  inputs?: string[];
  params?: Record<string, unknown>;
}

interface WorkflowEdgeSpec {
  source: string;
  target: string;
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
    const newNodes: Node[] = spec.nodes.map((n: WorkflowNodeSpec, i: number) => ({
      id: n.id,
      position: { x: 100, y: 100 + i * 150 },
      data: { label: `${n.id} (${n.type})` },
      type: n.type === 'input' ? 'input' : 'default'
    }));
    setNodes(newNodes);

    const newEdges: Edge[] = spec.edges.map((e: WorkflowEdgeSpec) => ({
      id: `e-${e.source}-${e.target}`,
      source: e.source,
      target: e.target
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

  const runWorkflow = async () => {
    if (!activeWorkflowId) return;
    try {
      const res = await axios.post(`${API_BASE}/runs/`, {
        workflow_id: activeWorkflowId,
        initial_input: { text: "Hello from UI" }
      });
      alert(`Run started! ID: ${res.data.run_id}`);
    } catch {
      alert("Run failed.");
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
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors cursor-pointer shadow-lg active:scale-95"
          >
            <Play className="w-4 h-4" /> Run
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
