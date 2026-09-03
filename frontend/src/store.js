import { reactive, computed } from 'vue'
import { api } from './api'

let seq = 0
export const nid = () => `${Date.now().toString(36)}${(seq++).toString(36)}${Math.random().toString(36).slice(2, 6)}`

export const state = reactive({
  mode: 'ai', // 'ai' | 'demo'
  model: '',
  view: 'create', // 'create' | 'play'
  story: emptyStory(),
  busy: null, // 正在生成的节点/选项 id，用于局部 loading
  toast: null,
  diagnostics: null,
  diagLoading: false,
  library: [],
})

export function emptyStory() {
  return {
    id: null,
    title: '',
    world: '',
    protagonist: '',
    premise: '',
    tone: '',
    characters: [],
    threads: [],
    root: null,
    nodes: {},
    updated: null,
  }
}

export const hasStory = computed(() => !!state.story.root && !!state.story.nodes[state.story.root])

export function node(id) {
  return state.story.nodes[id] || null
}

/** 从根节点到 targetId 的路径（含 targetId），每项带 chosen_label。 */
export function pathTo(targetId) {
  const out = []
  const walk = (id, chosen) => {
    const n = node(id)
    if (!n) return false
    out.push({ id, text: n.text, chosen_label: chosen })
    if (id === targetId) return true
    for (const o of n.options || []) {
      if (o.child && walk(o.child, o.label)) return true
    }
    out.pop()
    return false
  }
  if (state.story.root) walk(state.story.root, null)
  return out
}

/** 把 AI 提取的角色/伏笔并入故事圣经（去重）。 */
function mergeBible(characters, threads) {
  const known = new Set(state.story.characters.map((c) => c.name))
  for (const c of characters || []) {
    if (c.name && !known.has(c.name)) {
      state.story.characters.push(c)
      known.add(c.name)
    }
  }
  const tset = new Set(state.story.threads)
  for (const t of threads || []) {
    if (t && !tset.has(t)) {
      state.story.threads.push(t)
      tset.add(t)
    }
  }
}

export function notify(msg, kind = 'ok') {
  state.toast = { msg, kind }
  setTimeout(() => {
    if (state.toast && state.toast.msg === msg) state.toast = null
  }, 3200)
}

/** 无 key 时后端返回 mock；_degraded 表示真实调用失败已降级。 */
function flagSource(res) {
  if (res._mock) notify('当前为演示模式（未配置 API Key），内容为本地生成器产出', 'warn')
  else if (res._degraded) notify('AI 调用失败，本次已降级为演示内容', 'warn')
}

// ---------------------------------------------------------------- 生成动作

export async function generateOpening() {
  state.busy = 'opening'
  try {
    const res = await api.opening(state.story)
    flagSource(res)
    const id = nid()
    state.story.nodes = {}
    state.story.root = id
    if (res.title) state.story.title = res.title
    state.story.nodes[id] = {
      id,
      text: res.text,
      is_ending: false,
      ending_type: '',
      options: res.options || [],
    }
    mergeBible(res.characters, res.threads)
    state.diagnostics = null
  } catch (e) {
    notify('开篇生成失败：' + e.message, 'err')
  } finally {
    state.busy = null
  }
}

export async function expandOption(optionId) {
  const found = findOption(optionId)
  if (!found) return
  const { node: parent, option } = found
  state.busy = optionId
  try {
    const path = pathTo(parent.id)
    const res = await api.continuation(state.story, path, option.label)
    flagSource(res)
    const id = nid()
    state.story.nodes[id] = {
      id,
      text: res.text,
      is_ending: false,
      ending_type: '',
      options: res.options || [],
    }
    option.child = id
    mergeBible(res.characters, res.threads)
    state.diagnostics = null
  } catch (e) {
    notify('续写失败：' + e.message, 'err')
  } finally {
    state.busy = null
  }
}

/** 重新生成某选项下的分支（丢弃旧子树）。 */
export async function rerollOption(optionId) {
  const found = findOption(optionId)
  if (!found) return
  if (found.option.child) dropSubtree(found.option.child)
  found.option.child = null
  await expandOption(optionId)
}

export async function makeEnding(optionId) {
  const found = findOption(optionId)
  if (!found) return
  const { node: parent, option } = found
  state.busy = optionId
  try {
    const path = pathTo(parent.id)
    const res = await api.ending(state.story, path)
    flagSource(res)
    const id = nid()
    state.story.nodes[id] = {
      id,
      text: res.text,
      is_ending: true,
      ending_type: res.ending_type || '结局',
      options: [],
    }
    option.child = id
    state.diagnostics = null
  } catch (e) {
    notify('结局生成失败：' + e.message, 'err')
  } finally {
    state.busy = null
  }
}

/** 把已有节点直接标记为结局（用其自身文本收尾，不调用 AI）。 */
export function markEnding(nodeId) {
  const n = node(nodeId)
  if (!n) return
  n.is_ending = true
  n.ending_type = n.ending_type || '自定义结局'
  n.options = []
  state.diagnostics = null
}

export function findOption(optionId) {
  for (const n of Object.values(state.story.nodes)) {
    for (const o of n.options || []) {
      if (o.id === optionId) return { node: n, option: o }
    }
  }
  return null
}

export function dropSubtree(rootId) {
  const n = node(rootId)
  if (!n) return
  for (const o of n.options || []) {
    if (o.child) dropSubtree(o.child)
  }
  delete state.story.nodes[rootId]
}

export function deleteNode(nodeId) {
  if (nodeId === state.story.root) {
    state.story.root = null
    state.story.nodes = {}
    return
  }
  for (const n of Object.values(state.story.nodes)) {
    for (const o of n.options || []) {
      if (o.child === nodeId) {
        o.child = null
        break
      }
    }
  }
  dropSubtree(nodeId)
  state.diagnostics = null
}

export function addManualOption(nodeId) {
  const n = node(nodeId)
  if (!n || n.is_ending) return
  if ((n.options || []).length >= 4) return notify('单个节点最多 4 个选项', 'warn')
  n.options.push({ id: nid(), label: '新选项', hint: '', child: null })
}

// ---------------------------------------------------------------- 诊断

export async function runDiagnose() {
  state.diagLoading = true
  try {
    state.diagnostics = await api.diagnose(state.story)
  } catch (e) {
    notify('诊断失败：' + e.message, 'err')
  } finally {
    state.diagLoading = false
  }
}

// ---------------------------------------------------------------- 持久化

export async function saveStory() {
  try {
    state.story.updated = new Date().toISOString()
    const res = await api.saveStory(state.story)
    state.story.id = res.id
    notify('已保存到本地作品库')
  } catch (e) {
    notify('保存失败：' + e.message, 'err')
  }
}

export async function loadLibrary() {
  try {
    state.library = await api.listStories()
  } catch (e) {
    state.library = []
  }
}

export async function openStory(id) {
  try {
    const s = await api.getStory(id)
    state.story = { ...emptyStory(), ...s }
    state.diagnostics = null
    notify('已载入《' + (s.title || '未命名') + '》')
  } catch (e) {
    notify('载入失败：' + e.message, 'err')
  }
}

export async function removeStory(id) {
  await api.deleteStory(id)
  await loadLibrary()
}

export function newStory() {
  state.story = emptyStory()
  state.diagnostics = null
  state.view = 'create'
}

// ---------------------------------------------------------------- 统计

export const stats = computed(() => {
  const nodes = Object.values(state.story.nodes)
  const endings = nodes.filter((n) => n.is_ending)
  const pending = nodes.reduce(
    (acc, n) => acc + (n.is_ending ? 0 : (n.options || []).filter((o) => !o.child).length),
    0,
  )
  const words = nodes.reduce((a, n) => a + (n.text || '').length, 0)
  return { nodes: nodes.length, endings: endings.length, pending, words }
})

export async function initStatus() {
  try {
    const s = await api.status()
    state.mode = s.mode === 'AI' ? 'ai' : 'demo'
    state.model = s.model
  } catch (e) {
    state.mode = 'demo'
    state.model = 'unreachable'
  }
}
