// NexT uses non-native button elements. Support keyboard activation as well.
document.addEventListener('keydown', event => {
  const button = event.target.closest('[role="button"]');
  if (!button || button !== event.target || button.tagName === 'BUTTON') return;
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    button.click();
  }
});
// Preview traffic must not show the shared localhost counter as personal visits.
if (location.hostname === 'sysufyj.github.io') {
  const counter = document.createElement('script');
  counter.async = true;
  counter.src = 'https://busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js';
  document.head.append(counter);
} else {
  document.querySelectorAll('.busuanzi-count, #busuanzi_container_page_pv').forEach(el => { el.hidden = true; });
}
