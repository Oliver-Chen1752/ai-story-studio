<script setup>
import { onMounted, ref } from 'vue'
import {
  state, hasStory, newStory, saveStory,
  openStory, loadLibrary, removeStory, initStatus,
} from './store'
import SetupPanel from './components/SetupPanel.vue'
import NodeCard from './components/NodeCard.vue'
import StructurePanel from './components/StructurePanel.vue'
import BiblePanel from './components/BiblePanel.vue'
import PlayMode from './components/PlayMode.vue'

const libOpen = ref(false)

onMounted(async () => {
  await initStatus()
  loadLibrary()
})

function toggleLib() {
  libOpen.value = !libOpen.value
  if (libOpen.value) loadLibrary()
}

function pickStory(id) {
  openStory(id)
  libOpen.value = false
  state.view = 'create'
}
</script>

<template>
  <header class="top">
    <div class="brand">
      <span class="logo">⑂</span>
      <div>
        <b>Ai故事工坊</b>
        <span class="slogan">AI 互动故事创作器</span>
      </div>
    </div>

    <div class="title-zone">
      <input v-if="state.view === 'create'" v-model="state.story.title" class="story-title" placeholder="未命名作品" maxlength="20" />
      <span v-else class="story-title static">《{{ state.story.title || '未命名' }}》· 试玩中</span>
    </div>

    <div class="top-acts">
      <span class="mode" :class="state.mode" :title="state.mode === 'ai' ? 'AI 生成已启用' : '未配置 API Key，使用本地演示生成器'">
        <i></i>{{ state.mode === 'ai' ? 'AI · ' + state.model : '演示模式' }}
      </span>
      <div class="seg">
        <button :class="{ on: state.view === 'create' }" @click="state.view = 'create'">创作</button>
        <button :class="{ on: state.view === 'play' }" :disabled="!hasStory" @click="state.view = 'play'">▶ 试玩</button>
      </div>
      <button class="mini" @click="toggleLib">作品库</button>
      <button class="mini solid" :disabled="!hasStory" @click="saveStory">保存</button>
      <button class="mini" @click="newStory">新建</button>
    </div>
  </header>

  <main v-if="state.view === 'create'" class="work">
    <section class="left">
      <SetupPanel />
      <div class="canvas">
        <h2 class="sec-title"><span class="step-dot">2</span>故事树 <small>在选项上点「AI 续写」展开分支</small></h2>
        <NodeCard v-if="hasStory" :id="state.story.root" :depth="0" />
        <div v-else-if="state.busy === 'opening'" class="loading">
          <span class="spin big"></span>AI 正在构思开篇与第一组分歧……
        </div>
        <p v-else class="empty">填写上方设定，点击「生成开篇」开始创作。</p>
      </div>
    </section>
    <section class="right">
      <StructurePanel />
      <BiblePanel />
    </section>
  </main>

  <main v-else class="work single">
    <PlayMode />
  </main>

  <!-- 作品库抽屉 -->
  <div v-if="libOpen" class="drawer-mask" @click.self="libOpen = false">
    <div class="drawer">
      <div class="d-head">
        <h3>本地作品库</h3>
        <button class="mini" @click="libOpen = false">✕</button>
      </div>
      <p v-if="!state.library.length" class="empty">还没有保存过作品。</p>
      <div v-for="s in state.library" :key="s.id" class="lib-item">
        <div class="li-main" @click="pickStory(s.id)">
          <b>{{ s.title }}</b>
          <span>{{ s.nodes }} 节点 · {{ s.endings }} 结局</span>
        </div>
        <button class="mini danger" @click.stop="removeStory(s.id)">删</button>
      </div>
    </div>
  </div>

  <!-- toast -->
  <transition name="t">
    <div v-if="state.toast" class="toast" :class="state.toast.kind">{{ state.toast.msg }}</div>
  </transition>
</template>

<style scoped>
.top {
  display: flex; align-items: center; gap: 18px; padding: 10px 18px;
  background: var(--bg2); border-bottom: 1px solid var(--line);
  position: sticky; top: 0; z-index: 20;
}
.brand { display: flex; align-items: center; gap: 10px; }
.logo { font-size: 24px; color: var(--accent); }
.brand b { display: block; font-size: 15px; }
.slogan { font-size: 11px; color: var(--muted); }
.title-zone { flex: 1; min-width: 0; }
.story-title {
  background: transparent; border: 1px solid transparent; border-radius: 8px;
  color: var(--fg); font-size: 16px; font-weight: 600; padding: 5px 10px; width: 100%; max-width: 320px;
}
.story-title:focus { outline: none; border-color: var(--line); background: var(--bg); }
.story-title.static { display: inline-block; }
.top-acts { display: flex; align-items: center; gap: 10px; }
.mode {
  font-size: 11.5px; padding: 4px 10px; border-radius: 999px; display: inline-flex; align-items: center; gap: 6px;
  border: 1px solid var(--line); color: var(--muted);
}
.mode i { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); }
.mode.ai { color: var(--ok); border-color: var(--ok); }
.mode.ai i { background: var(--ok); box-shadow: 0 0 6px var(--ok); }
.mode.demo { color: var(--warn); border-color: var(--warn); }
.mode.demo i { background: var(--warn); }
.seg { display: flex; border: 1px solid var(--line); border-radius: 9px; overflow: hidden; }
.seg button {
  background: transparent; border: none; color: var(--muted); padding: 6px 14px;
  font-size: 13px; cursor: pointer;
}
.seg button.on { background: var(--accent); color: #fff; }
.seg button:disabled { opacity: .4; cursor: default; }
.mini {
  background: var(--bg3); border: 1px solid var(--line); color: var(--muted);
  border-radius: 7px; padding: 6px 12px; font-size: 12.5px; cursor: pointer;
}
.mini:hover:not(:disabled) { color: var(--fg); border-color: var(--accent); }
.mini:disabled { opacity: .45; cursor: default; }
.mini.solid { background: var(--accent); border-color: var(--accent); color: #fff; }
.mini.danger:hover { color: #ff6b6b; border-color: #ff6b6b; }

.work {
  display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 18px;
  max-width: 1280px; margin: 0 auto; padding: 18px; align-items: start;
}
.work.single { display: block; }
.left { min-width: 0; }
.canvas { padding: 20px; }
.sec-title { font-size: 15px; margin: 0 0 14px; display: flex; align-items: baseline; gap: 8px; }
.sec-title small { font-size: 12px; color: var(--muted); font-weight: 400; }
.step-dot {
  width: 20px; height: 20px; border-radius: 50%; background: var(--accent);
  color: #fff; font-size: 12px; display: inline-flex; align-items: center; justify-content: center;
  align-self: center;
}
.loading { display: flex; align-items: center; gap: 10px; color: var(--muted); padding: 40px 0; font-size: 14px; }
.spin { width: 14px; height: 14px; border: 2px solid var(--line); border-top-color: var(--accent); border-radius: 50%; animation: rot .8s linear infinite; display: inline-block; }
.spin.big { width: 20px; height: 20px; }
@keyframes rot { to { transform: rotate(360deg); } }
.empty { color: var(--muted); font-size: 13.5px; padding: 30px 0; text-align: center; }
.right { display: flex; flex-direction: column; gap: 14px; position: sticky; top: 74px; }

.drawer-mask { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 40; display: flex; justify-content: flex-end; }
.drawer {
  width: 340px; background: var(--bg2); border-left: 1px solid var(--line);
  padding: 18px; overflow-y: auto; animation: slide .25s ease;
}
@keyframes slide { from { transform: translateX(40px); opacity: 0; } }
.d-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.d-head h3 { margin: 0; font-size: 15px; }
.lib-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.li-main {
  flex: 1; background: var(--bg3); border: 1px solid var(--line); border-radius: 9px;
  padding: 10px 12px; cursor: pointer; display: flex; flex-direction: column; gap: 3px; min-width: 0;
}
.li-main:hover { border-color: var(--accent); }
.li-main b { font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.li-main span { font-size: 11.5px; color: var(--muted); }

.toast {
  position: fixed; bottom: 26px; left: 50%; transform: translateX(-50%);
  background: var(--bg3); border: 1px solid var(--line); color: var(--fg);
  padding: 10px 18px; border-radius: 10px; font-size: 13px; z-index: 60; max-width: 80vw;
  box-shadow: 0 8px 30px rgba(0,0,0,.4);
}
.toast.warn { border-color: var(--warn); color: var(--warn); }
.toast.err { border-color: var(--err); color: var(--err); }
.t-enter-active, .t-leave-active { transition: all .25s ease; }
.t-enter-from, .t-leave-to { opacity: 0; transform: translate(-50%, 10px); }

@media (max-width: 900px) {
  .work { grid-template-columns: 1fr; }
  .right { position: static; }
}
</style>
