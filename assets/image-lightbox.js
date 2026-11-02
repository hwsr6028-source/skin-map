/* Article image viewer. Images stay real <img> elements in generated HTML.
   Images wrapped in a user-specified link keep their destination on click. */
(() => {
  'use strict';
  const article = document.querySelector('.article');
  if (!article) return;

  const dialog = document.createElement('dialog');
  dialog.className = 'article-image-dialog';
  dialog.setAttribute('aria-label', '본문 이미지 크게 보기');

  const viewer = document.createElement('div');
  viewer.className = 'article-image-dialog-viewer';

  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'article-image-dialog-close';
  close.setAttribute('aria-label', '이미지 닫기');
  close.textContent = '×';

  const image = document.createElement('img');
  image.alt = '';
  image.decoding = 'async';

  const caption = document.createElement('p');
  caption.className = 'article-image-dialog-caption';

  viewer.append(close, image, caption);
  dialog.append(viewer);
  document.body.append(dialog);

  const dismiss = () => {
    if (dialog.open) dialog.close();
  };

  close.addEventListener('click', dismiss);
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dismiss();
  });
  dialog.addEventListener('close', () => {
    image.removeAttribute('src');
    document.body.style.removeProperty('overflow');
  });

  article.querySelectorAll('img').forEach(img => {
    // A linked image must still follow the link specified by the author.
    if (img.closest('a[href]')) return;
    img.classList.add('article-image-zoomable');
    img.setAttribute('tabindex', '0');
    img.setAttribute('role', 'button');
    img.setAttribute('aria-label', (img.alt || '본문 이미지') + ' 크게 보기');

    const open = () => {
      image.src = img.currentSrc || img.src;
      image.alt = img.alt || '본문 이미지 확대';
      caption.textContent = img.alt || '';
      document.body.style.overflow = 'hidden';
      if (typeof dialog.showModal === 'function') dialog.showModal();
      else {
        // Older browsers: use native image URL rather than fake popup.
        document.body.style.removeProperty('overflow');
        window.open(image.src, '_blank', 'noopener,noreferrer');
      }
    };
    img.addEventListener('click', open);
    img.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        open();
      }
    });
  });
})();
