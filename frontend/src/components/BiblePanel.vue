<script setup>
import { state } from '../store'
</script>

<template>
  <aside class="bible">
    <h3>故事圣经 <span class="sub">AI 续写时的上下文来源</span></h3>
    <div class="grp">
      <span class="lbl">已确立角色</span>
      <div v-if="state.story.characters.length" class="chars">
        <div v-for="(c, i) in state.story.characters" :key="i" class="char">
          <b>{{ c.name }}</b><span>{{ c.desc }}</span>
        </div>
      </div>
      <p v-else class="none">生成节点后自动登记</p>
    </div>
    <div class="grp">
      <span class="lbl">伏笔 / 悬念</span>
      <ul v-if="state.story.threads.length" class="threads">
        <li v-for="(t, i) in state.story.threads" :key="i">{{ t }}</li>
      </ul>
      <p v-else class="none">暂无</p>
    </div>
  </aside>
</template>

<style scoped>
.bible { background: var(--bg2); border: 1px solid var(--line); border-radius: 12px; padding: 14px; }
h3 { margin: 0 0 12px; font-size: 14px; }
.sub { font-size: 11px; color: var(--muted); font-weight: 400; margin-left: 4px; }
.grp { margin-bottom: 12px; }
.lbl { font-size: 11px; color: var(--muted); display: block; margin-bottom: 6px; }
.chars { display: flex; flex-direction: column; gap: 6px; }
.char { background: var(--bg3); border-radius: 8px; padding: 7px 9px; font-size: 12.5px; }
.char b { color: var(--accent); margin-right: 6px; }
.char span { color: var(--muted); }
.threads { margin: 0; padding-left: 16px; display: flex; flex-direction: column; gap: 4px; }
.threads li { font-size: 12.5px; color: var(--fg); line-height: 1.55; }
.none { font-size: 12px; color: var(--muted); margin: 0; font-style: italic; }
</style>
