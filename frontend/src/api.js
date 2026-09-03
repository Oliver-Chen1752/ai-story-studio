const BASE = '/api'

async function post(url, body) {
  const res = await fetch(BASE + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  })
  if (!res.ok) throw new Error(`${url} -> ${res.status}`)
  return res.json()
}

async function get(url) {
  const res = await fetch(BASE + url)
  if (!res.ok) throw new Error(`${url} -> ${res.status}`)
  return res.json()
}

export const api = {
  status: () => get('/status'),
  opening: (story) => post('/story/opening', story),
  continuation: (story, path, chosen_label) => post('/story/continue', { story, path, chosen_label }),
  ending: (story, path) => post('/story/ending', { story, path }),
  diagnose: (story) => post('/story/diagnose', story),
  listStories: () => get('/stories'),
  getStory: (id) => get(`/stories/${id}`),
  saveStory: (story) => post('/stories', story),
  deleteStory: (id) => fetch(`${BASE}/stories/${id}`, { method: 'DELETE' }).then((r) => r.json()),
}
