<script setup>
import { state, generateOpening, hasStory } from '../store'

const tones = ['冷峻悬疑', '温暖治愈', '黑色幽默', '史诗奇幻', '科幻惊悚', '武侠']
</script>

<template>
  <section class="setup">
    <h2 class="sec-title"><span class="step-dot">1</span>故事设定</h2>
    <div class="grid">
      <label class="field">
        <span>世界观</span>
        <input v-model="state.story.world" placeholder="例：一座被永恒浓雾困住的滨海城市" maxlength="80" />
      </label>
      <label class="field">
        <span>主角</span>
        <input v-model="state.story.protagonist" placeholder="例：林澈，28岁，替人寻物的私家侦探" maxlength="60" />
      </label>
      <label class="field wide">
        <span>故事前提（核心事件）</span>
        <textarea v-model="state.story.premise" rows="2" placeholder="例：一位老妇人出价十万，请他在雾中找到失踪三十年的女儿" maxlength="200"></textarea>
      </label>
      <label class="field wide">
        <span>基调</span>
        <div class="tones">
          <button
            v-for="t in tones" :key="t"
            class="tone" :class="{ on: state.story.tone === t }"
            @click="state.story.tone = state.story.tone === t ? '' : t"
          >{{ t }}</button>
        </div>
      </label>
    </div>
    <button
      class="primary"
      :disabled="!state.story.premise.trim() || state.busy === 'opening'"
      @click="generateOpening"
    >
      <span v-if="state.busy === 'opening'" class="spin"></span>
      {{ hasStory ? '重新生成开篇' : '✦ 生成开篇' }}
    </button>
    <p v-if="hasStory" class="hint">重新生成将丢弃当前整棵故事树（可先保存）。</p>
  </section>
</template>

<style scoped>
.setup { padding: 20px; border-bottom: 1px solid var(--line); }
.sec-title { font-size: 15px; margin: 0 0 14px; display: flex; align-items: center; gap: 8px; }
.step-dot {
  width: 20px; height: 20px; border-radius: 50%; background: var(--accent);
  color: #fff; font-size: 12px; display: inline-flex; align-items: center; justify-content: center;
}
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--muted); }
.field.wide { grid-column: 1 / -1; }
.field input, .field textarea {
  background: var(--bg2); border: 1px solid var(--line); border-radius: 8px;
  color: var(--fg); padding: 9px 11px; font-size: 14px; font-family: inherit; resize: vertical;
}
.field input:focus, .field textarea:focus { outline: none; border-color: var(--accent); }
.tones { display: flex; flex-wrap: wrap; gap: 8px; }
.tone {
  background: var(--bg2); border: 1px solid var(--line); color: var(--muted);
  border-radius: 999px; padding: 4px 12px; font-size: 12px; cursor: pointer;
}
.tone.on { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); }
.primary {
  margin-top: 14px; width: 100%; padding: 11px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #6c5ce7, #8e7cf3); color: #fff;
  font-size: 15px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
}
.primary:disabled { opacity: .45; cursor: not-allowed; }
.primary:not(:disabled):hover { filter: brightness(1.1); }
.hint { font-size: 12px; color: var(--warn); margin: 8px 0 0; }
.spin { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.4); border-top-color: #fff; border-radius: 50%; animation: rot .8s linear infinite; }
@keyframes rot { to { transform: rotate(360deg); } }
</style>
