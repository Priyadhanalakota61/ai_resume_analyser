/* All provider/model strings become text nodes, never HTML. */
const csrf = document.querySelector('meta[name="csrf-token"]').content;
const cards = [...document.querySelectorAll('.job')];
const running = new Map();
function element(tag, text, parent, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  if (parent) parent.append(node);
  return node;
}
function list(title, values, parent) {
  element('h3', title, parent);
  const ul = element('ul', undefined, parent);
  (values.length ? values : ['None identified.']).forEach(v => element('li', v, ul));
}
function render(card, data) {
  const area = card.querySelector('.outcome');
  area.replaceChildren();
  if (data.status !== 'complete') { element('p', data.message, area, 'error'); return; }
  const r = data.result;
  element('div', r.job_match_score === null ? 'Score unavailable' : `${r.job_match_score}%`, area, 'score');
  element('p', 'Job-match estimate · matched requirements / all identified requirements × 100', area, 'muted');
  const cols = element('div', undefined, area, 'columns');
  list('Strengths', r.strengths, element('div', undefined, cols));
  list('Gaps · evidence not found', r.gaps, element('div', undefined, cols, 'gap'));
  const evidence = element('details', undefined, area);
  element('summary', 'Requirements & supporting excerpts', evidence);
  r.requirements.forEach(req => {
    element('h4', `${req.requirement} — ${req.status === 'matched' ? 'Matched' : 'Not found'}`, evidence);
    element('p', `Posting: ${req.job_evidence}`, evidence);
    if (req.resume_evidence) element('p', `Resume: ${req.resume_evidence}`, evidence);
  });
  const questions = element('details', undefined, area);
  element('summary', 'Interview practice questions', questions);
  const ol = element('ol', undefined, questions);
  r.interview_questions.forEach(q => element('li', q, ol));
  list('Suggestions', r.suggestions, area);
  element('p', data.saved ? `Saved to MySQL · record #${data.record_id}` : `Analysis displayed but not saved: ${data.message}`, area, data.saved ? 'muted' : 'error');
}
async function analyze(card) {
  if (running.has(card)) return running.get(card);
  const task = (async () => {
    const button = card.querySelector('button'); button.disabled = true;
    card.querySelector('.outcome').textContent = 'Analysing this posting…';
    try {
      const response = await fetch(card.dataset.url, {method:'POST', headers:{'X-CSRF-Token':csrf}});
      if (!response.ok) throw new Error(response.status === 410 ? 'Search expired. Upload the resume again.' : 'Request failed. Reload the page before retrying.');
      render(card, await response.json());
      button.textContent = 'Show cached result';
    } catch (error) { card.querySelector('.outcome').textContent = error.message; }
    finally { button.disabled = false; }
  })();
  running.set(card, task);
  await task; running.delete(card);
}
cards.forEach(card => card.querySelector('button').addEventListener('click', () => analyze(card)));
const all = document.getElementById('analyze-all');
if (all) all.addEventListener('click', async () => {
  all.disabled = true;
  for (const [i, card] of cards.entries()) {
    document.getElementById('progress').textContent = `Analysing ${i+1} of ${cards.length}…`;
    await analyze(card);
  }
  document.getElementById('progress').textContent = 'Finished. Each card shows its result or availability message.';
  all.disabled = false;
});
// The preceding search button explicitly requests fit comparison; progressively start it.
if (all) all.click();
