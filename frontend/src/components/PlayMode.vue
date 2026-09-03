<script setup>
import { ref, computed } from 'vue'
import { state, node } from '../store'

const cur = ref(state.story.root)
const trail = ref([])

const n = computed(() => node(cur.value))

function choose(o) {
  if (!o.child) return
  trail.value.push({ from: cur.value, label: o.label })
  cur.value = o.child
}
function back() {
  const p = trail.value.pop()
  if (p) cur.value = p.from
}
function restart() {
  cur.value = state.story.root
  trail.value = []
}
</script>

<template>
  <div class="play">
    <div class="play-bar">
      <button class="mini" :disabled="!trail.length" @click="back">← 上一步</button>
      <span class="prog">第 {{ trail.length + 1 }} 幕</span>
      <button class="mini" @click="restart">↺ 重新开始</button>
    </div>

    <article v-if="n" class="scene">
      <p class="scene-text">{{ n.text }}</p>

      <div v-if="n.is_ending" class="ending">
        <span class="badge">◈ {{ n.ending_type || '结局' }}</span>
        <p class="ending-tip">—— 本条故事线到此结束 ——</p>
        <button class="primary" @click="restart">重新体验</button>
      </div>

      <div v-else class="choices">
        <p class="ask">你要怎么做？</p>
        <button
          v-for="o in n.options" :key="o.id"
          class="choice" :class="{ off: !o.child }"
          :disabled="!o.child"
          @click="choose(o)"
        >
          <span class="cl">{{ o.label }}</span>
          <span class="ch" v-if="o.hint">{{ o.hint }}</span>
          <span class="unbuilt" v-if="!o.child">（此分支尚未展开，回创作模式用 AI 续写）</span>
        </button>
      </div>
    </article>
    <p v-else class="empty">故事还没有开篇，请先在创作模式生成。</p>
  </div>
</template>

<style scoped>
.play { max-width: 680px; margin: 0 auto; padding: 24px 20px 60px; }
.play-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.prog { font-size: 12.5px; color: var(--muted); }
.scene { animation: fade .35s ease; }
@keyframes fade { from { opacity: 0; transform: translateY(8px); } }
.scene-text { white-space: pre-wrap; line-height: 2; font-size: 16.5px; color: var(--fg); }
.ending { text-align: center; margin-top: 30px; padding-top: 24px; border-top: 1px solid var(--gold); }
.badge { display: inline-block; font-size: 14px; color: var(--gold); border: 1px solid var(--gold); border-radius: 999px; padding: 5px 16px; margin-bottom: 10px; }
.ending-tip { color: var(--muted); font-size: 13px; }
.choices { margin-top: 30px; }
.ask { font-size: 14px; color: var(--muted); margin: 0 0 12px; }
.choice {
  display: flex; flex-direction: column; gap: 4px; text-align: left; width: 100%;
  background: var(--bg2); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px 16px; margin-bottom: 10px; cursor: pointer; transition: all .15s;
}
.choice:not(:disabled):hover { border-color: var(--accent); background: var(--accent-soft); transform: translateX(3px); }
.choice.off { opacity: .5; cursor: not-allowed; }
.cl { font-size: 15px; font-weight: 600; color: var(--fg); }
.ch { font-size: 12.5px; color: var(--muted); }
.unbuilt { font-size: 11.5px; color: var(--warn); }
.primary { margin-top: 16px; padding: 10px 26px; border: none; border-radius: 10px; background: linear-gradient(135deg,#6c5ce7,#8e7cf3); color: #fff; font-size: 15px; cursor: pointer; }
.empty { color: var(--muted); text-align: center; padding: 60px 0; }
.mini { background: var(--bg2); border: 1px solid var(--line); color: var(--muted); border-radius: 7px; padding: 5px 12px; font-size: 12.5px; cursor: pointer; }
.mini:disabled { opacity: .4; cursor: default; }
</style>
