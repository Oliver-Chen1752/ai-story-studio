<script>
export default { name: 'NodeCard' }
</script>

<script setup>
import { ref } from 'vue'
import {
  state, node, expandOption, rerollOption, makeEnding,
  markEnding, addManualOption, deleteNode,
} from '../store'

const props = defineProps({ id: String, depth: { type: Number, default: 0 } })

const n = () => node(props.id)
const editing = ref(false)
const draft = ref('')

function startEdit() {
  draft.value = n().text
  editing.value = true
}
function saveEdit() {
  n().text = draft.value.trim() || n().text
  editing.value = false
}
function cancelEdit() {
  editing.value = false
}
</script>

<template>
  <div v-if="n()" class="card" :class="{ ending: n().is_ending }" :style="{ '--d': depth }">
    <div class="card-head">
      <span class="tag" v-if="n().is_ending">◈ {{ n().ending_type || '结局' }}</span>
      <span class="tag root" v-else-if="depth === 0">开篇</span>
      <span class="wc">{{ (n().text || '').length }} 字</span>
      <div class="acts">
        <button class="mini" @click="editing ? cancelEdit() : startEdit()">{{ editing ? '取消' : '编辑' }}</button>
        <button v-if="!n().is_ending" class="mini" @click="markEnding(n().id)">标为结局</button>
        <button class="mini danger" @click="deleteNode(n().id)">删除</button>
      </div>
    </div>

    <p v-if="!editing" class="text">{{ n().text }}</p>
    <div v-else class="edit">
      <textarea v-model="draft" rows="10"></textarea>
      <div class="edit-acts">
        <button class="mini save" @click="saveEdit">保存修改</button>
      </div>
    </div>

    <!-- 选项列表 -->
    <div v-if="!n().is_ending" class="opts">
      <div v-for="o in n().options" :key="o.id" class="opt">
        <div class="opt-main">
          <div class="opt-top">
            <span class="arrow">↳</span>
            <input v-model="o.label" class="opt-label" maxlength="30" />
          </div>
          <input v-model="o.hint" class="opt-hint" placeholder="后果提示（可选）" maxlength="40" />
        </div>
        <div class="opt-acts">
          <template v-if="!o.child">
            <button
              class="mini gen" :disabled="state.busy === o.id"
              @click="expandOption(o.id)"
            >
              <span v-if="state.busy === o.id" class="spin"></span>
              {{ state.busy === o.id ? 'AI 续写中' : '✦ AI 续写' }}
            </button>
            <button class="mini" :disabled="state.busy === o.id" @click="makeEnding(o.id)">✦ 收为结局</button>
          </template>
          <template v-else>
            <button class="mini" :disabled="state.busy === o.id" @click="rerollOption(o.id)">
              <span v-if="state.busy === o.id" class="spin"></span>重roll
            </button>
            <button class="mini danger" @click="o.child = null">收起</button>
          </template>
        </div>

        <!-- 递归子节点 -->
        <NodeCard v-if="o.child" :id="o.child" :depth="depth + 1" class="nested" />
      </div>

      <button class="mini add" @click="addManualOption(n().id)">+ 手动添加选项</button>

      <div v-if="!(n().options || []).length" class="noopt">
        此节点没有选项，玩家会卡住 ——
        <button class="mini" @click="addManualOption(n().id)">添加选项</button>
        或
        <button class="mini" @click="markEnding(n().id)">标为结局</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--bg2); border: 1px solid var(--line); border-radius: 12px;
  padding: 14px 16px; margin-bottom: 14px;
}
.card.ending { border-color: var(--gold); background: var(--gold-soft); }
.card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.tag {
  font-size: 11px; padding: 2px 8px; border-radius: 999px;
  background: var(--gold-soft); color: var(--gold); border: 1px solid var(--gold);
}
.tag.root { background: var(--accent-soft); color: var(--accent); border-color: var(--accent); }
.wc { font-size: 11px; color: var(--muted); }
.acts { margin-left: auto; display: flex; gap: 6px; }
.text { white-space: pre-wrap; line-height: 1.85; font-size: 14.5px; margin: 0 0 12px; }
.edit textarea {
  width: 100%; box-sizing: border-box; background: var(--bg); color: var(--fg);
  border: 1px solid var(--accent); border-radius: 8px; padding: 10px;
  font-family: inherit; font-size: 14px; line-height: 1.7; resize: vertical;
}
.edit-acts { margin-top: 8px; }
.opts { border-top: 1px dashed var(--line); padding-top: 12px; }
.opt { margin-bottom: 12px; }
.opt-main { display: flex; flex-direction: column; gap: 6px; }
.opt-top { display: flex; align-items: center; gap: 8px; }
.arrow { color: var(--accent); font-weight: 700; }
.opt-label, .opt-hint {
  background: transparent; border: none; border-bottom: 1px dashed var(--line);
  color: var(--fg); font-size: 14px; font-family: inherit; padding: 3px 2px;
}
.opt-label { font-weight: 600; flex: 1; }
.opt-hint { font-size: 12px; color: var(--muted); }
.opt-label:focus, .opt-hint:focus { outline: none; border-bottom-color: var(--accent); }
.opt-acts { display: flex; gap: 6px; margin-top: 6px; }
.nested { margin-left: 14px; border-left: 2px solid var(--line); padding-left: 14px; margin-top: 10px; margin-bottom: 0; }
.nested :deep(.card) { background: var(--bg3); }
.add { margin-top: 2px; }
.noopt {
  font-size: 12.5px; color: var(--warn); background: var(--warn-soft);
  border-radius: 8px; padding: 8px 10px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
}
.mini {
  background: var(--bg3); border: 1px solid var(--line); color: var(--muted);
  border-radius: 7px; padding: 4px 10px; font-size: 12px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 5px;
}
.mini:hover:not(:disabled) { color: var(--fg); border-color: var(--accent); }
.mini:disabled { opacity: .5; cursor: default; }
.mini.gen { color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }
.mini.save { color: #fff; background: var(--accent); border-color: var(--accent); }
.mini.danger:hover { color: #ff6b6b; border-color: #ff6b6b; }
.spin { width: 10px; height: 10px; border: 2px solid var(--line); border-top-color: var(--accent); border-radius: 50%; animation: rot .8s linear infinite; }
@keyframes rot { to { transform: rotate(360deg); } }
</style>
