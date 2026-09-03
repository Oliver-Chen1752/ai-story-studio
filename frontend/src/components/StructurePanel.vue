<script setup>
import { computed } from 'vue'
import { state, node, stats, runDiagnose } from '../store'

const TYPE_LABEL = {
  dead_end: { t: '死路', c: 'err' },
  orphan: { t: '孤立节点', c: 'warn' },
  shallow: { t: '结局单薄', c: 'warn' },
  repetitive: { t: '内容雷同', c: 'warn' },
  shallow_path: { t: '铺垫不足', c: 'warn' },
}

/** 扁平化树，用于结构总览。 */
const rows = computed(() => {
  const out = []
  const walk = (id, depth, trail) => {
    const n = node(id)
    if (!n) return
    out.push({ id, depth, isEnding: !!n.is_ending, wc: (n.text || '').length, label: trail, opts: (n.options || []).length })
    for (const o of n.options || []) {
      if (o.child) walk(o.child, depth + 1, o.label)
    }
  }
  if (state.story.root) walk(state.story.root, 0, '')
  return out
})

const issueMap = computed(() => {
  const m = {}
  for (const it of state.diagnostics?.issues || []) {
    ;(m[it.node_id] = m[it.node_id] || []).push(it)
  }
  return m
})
</script>

<template>
  <aside class="panel">
    <div class="p-head">
      <h3>故事结构</h3>
      <button class="mini" :disabled="state.diagLoading || !stats.nodes" @click="runDiagnose">
        <span v-if="state.diagLoading" class="spin"></span>
        {{ state.diagLoading ? '诊断中' : '✦ 结构诊断' }}
      </button>
    </div>

    <div class="metrics">
      <div class="m"><b>{{ stats.nodes }}</b><span>节点</span></div>
      <div class="m"><b>{{ stats.endings }}</b><span>结局</span></div>
      <div class="m"><b>{{ stats.pending }}</b><span>待展开</span></div>
      <div class="m"><b>{{ stats.words }}</b><span>字数</span></div>
    </div>

    <div v-if="state.diagnostics" class="diag">
      <p class="d-sum">{{ state.diagnostics.summary }}</p>
      <ul v-if="state.diagnostics.issues.length" class="d-list">
        <li v-for="(it, i) in state.diagnostics.issues" :key="i" :class="TYPE_LABEL[it.type]?.c || 'warn'">
          <b>{{ TYPE_LABEL[it.type]?.t || it.type }}</b>{{ it.message }}
        </li>
      </ul>
      <p v-else class="d-ok">✓ 未发现结构问题</p>
    </div>

    <div class="tree">
      <div
        v-for="r in rows" :key="r.id"
        class="row" :style="{ paddingLeft: 8 + r.depth * 16 + 'px' }"
      >
        <span class="dot" :class="{ end: r.isEnding, bad: issueMap[r.id] }"></span>
        <span class="rlabel">{{ r.label || '开篇' }}</span>
        <span class="rmeta">{{ r.isEnding ? '结局' : r.opts + ' 选项' }} · {{ r.wc }}字</span>
      </div>
      <p v-if="!rows.length" class="empty">还没有内容，先在左侧生成开篇。</p>
    </div>
  </aside>
</template>

<style scoped>
.panel { background: var(--bg2); border: 1px solid var(--line); border-radius: 12px; padding: 14px; }
.p-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.p-head h3 { margin: 0; font-size: 14px; }
.metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 12px; }
.m { background: var(--bg3); border-radius: 8px; padding: 8px 4px; text-align: center; }
.m b { display: block; font-size: 16px; color: var(--accent); }
.m span { font-size: 11px; color: var(--muted); }
.diag { border-top: 1px dashed var(--line); padding-top: 10px; margin-bottom: 10px; }
.d-sum { font-size: 12.5px; color: var(--fg); margin: 0 0 8px; line-height: 1.6; }
.d-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.d-list li {
  font-size: 12px; line-height: 1.5; padding: 7px 9px; border-radius: 7px;
  background: var(--warn-soft); color: var(--warn);
}
.d-list li.err { background: var(--err-soft); color: var(--err); }
.d-list li b { margin-right: 6px; }
.d-ok { font-size: 12.5px; color: var(--ok); margin: 0; }
.tree { max-height: 46vh; overflow: auto; border-top: 1px dashed var(--line); padding-top: 8px; }
.row { display: flex; align-items: center; gap: 7px; padding: 4px 0; font-size: 12.5px; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--accent); flex: none; }
.dot.end { background: var(--gold); }
.dot.bad { background: var(--err); }
.rlabel { color: var(--fg); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 130px; }
.rmeta { margin-left: auto; color: var(--muted); font-size: 11px; flex: none; }
.empty { font-size: 12.5px; color: var(--muted); padding: 10px 0; }
.mini {
  background: var(--bg3); border: 1px solid var(--line); color: var(--accent);
  border-radius: 7px; padding: 4px 10px; font-size: 12px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 5px;
}
.mini:disabled { opacity: .5; cursor: default; }
.spin { width: 10px; height: 10px; border: 2px solid var(--line); border-top-color: var(--accent); border-radius: 50%; animation: rot .8s linear infinite; }
@keyframes rot { to { transform: rotate(360deg); } }
</style>
