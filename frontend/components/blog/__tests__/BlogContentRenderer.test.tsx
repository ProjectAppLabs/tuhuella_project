import React from 'react';
import { describe, it, expect, afterEach } from '@jest/globals';
import { act, render, screen, waitFor } from '@testing-library/react';
import { renderToString } from 'react-dom/server';
import { hydrateRoot } from 'react-dom/client';
import createDOMPurify from 'dompurify';

import BlogContentRenderer from '../BlogContentRenderer';

jest.mock('dompurify', () => ({
  __esModule: true,
  default: jest.fn((...args: unknown[]) => jest.requireActual<typeof createDOMPurify>('dompurify')(...args as Parameters<typeof createDOMPurify>)),
}));

const createPurifier = jest.mocked(createDOMPurify);
afterEach(() => { createPurifier.mockClear(); });

describe('BlogContentRenderer', () => {
  it('renders intro text from JSON content', () => {
    const contentJson = {
      intro: 'Adoptar es un acto de amor.',
      sections: [],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Adoptar es un acto de amor.')).toBeInTheDocument();
  });

  it('renders section heading and content', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { heading: 'Paso 1', content: 'Investiga refugios cercanos.' },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Paso 1')).toBeInTheDocument();
    expect(screen.getByText('Investiga refugios cercanos.')).toBeInTheDocument();
  });

  it('renders a list within a section', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { heading: 'Checklist', list: ['Vacunas', 'Esterilización', 'Microchip'] },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Vacunas')).toBeInTheDocument();
    expect(screen.getByText('Esterilización')).toBeInTheDocument();
    expect(screen.getByText('Microchip')).toBeInTheDocument();
  });

  it('renders subsections with title and description', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        {
          heading: 'Tipos',
          subsections: [
            { title: 'Adopción temporal', description: 'Cuidas al animal mientras encuentra hogar.' },
          ],
        },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Adopción temporal')).toBeInTheDocument();
    expect(screen.getByText('Cuidas al animal mientras encuentra hogar.')).toBeInTheDocument();
  });

  it('renders a quote block', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { quote: { text: 'La grandeza de una nación se mide por cómo trata a sus animales.', author: 'Mahatma Gandhi' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText(/La grandeza de una nación/)).toBeInTheDocument();
    expect(screen.getByText('— Mahatma Gandhi')).toBeInTheDocument();
  });

  it('renders a callout with title and text', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { callout: { type: 'warning', title: 'Importante', text: 'Consulta con un veterinario.' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Importante')).toBeInTheDocument();
    expect(screen.getByText('Consulta con un veterinario.')).toBeInTheDocument();
  });

  it('renders key takeaways', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { key_takeaways: ['Adoptar salva vidas', 'Esteriliza a tu mascota'] },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Adoptar salva vidas')).toBeInTheDocument();
    expect(screen.getByText('Esteriliza a tu mascota')).toBeInTheDocument();
  });

  it('renders FAQ items as details/summary elements', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { faq: [{ question: '¿Cuánto cuesta adoptar?', answer: 'Depende del refugio.' }] },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('¿Cuánto cuesta adoptar?')).toBeInTheDocument();
    expect(screen.getByText('Depende del refugio.')).toBeInTheDocument();
  });

  it('renders conclusion and CTA when present', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [],
      conclusion: 'Gracias por leer.',
      cta: '¡Adopta hoy!',
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Gracias por leer.')).toBeInTheDocument();
    expect(screen.getByText('¡Adopta hoy!')).toBeInTheDocument();
  });

  it('falls back to HTML content when JSON is empty', async () => {
    render(
      <BlogContentRenderer
        contentJson={null}
        contentHtml="<p>Contenido HTML</p>"
      />,
    );
    expect(await screen.findByText('Contenido HTML')).toBeInTheDocument();
  });

  it('renders empty state when no content is provided', () => {
    render(<BlogContentRenderer contentJson={null} contentHtml="" />);
    expect(screen.getByText('No hay contenido disponible.')).toBeInTheDocument();
  });

  it('renders an image with alt text', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { image: { url: 'http://example.com/img.jpg', alt: 'Perro feliz' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    const img = screen.getByAltText('Perro feliz');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', 'http://example.com/img.jpg');
  });

  it('renders timeline steps', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        {
          timeline: [
            { step: 'Paso 1', description: 'Visita el refugio.' },
            { step: 'Paso 2', description: 'Llena la solicitud.' },
          ],
        },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Visita el refugio.')).toBeInTheDocument();
    expect(screen.getByText('Llena la solicitud.')).toBeInTheDocument();
  });

  it('renders examples list', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { examples: ['Un perro pequeño', 'Un gato adulto'] },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Un perro pequeño')).toBeInTheDocument();
    expect(screen.getByText('Un gato adulto')).toBeInTheDocument();
  });

  it('renders info callout with correct icon and styling', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { callout: { type: 'info', title: 'Información', text: 'Este es un dato importante.' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Información')).toBeInTheDocument();
    expect(screen.getByText('Este es un dato importante.')).toBeInTheDocument();
  });

  it('renders note callout with correct icon and styling', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { callout: { type: 'note', text: 'Una nota sobre el proceso.' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Una nota sobre el proceso.')).toBeInTheDocument();
  });

  it('renders default callout when type is undefined', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { callout: { text: 'Consejo general sin tipo.' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Consejo general sin tipo.')).toBeInTheDocument();
  });

  it('renders YouTube video embed for standard youtube.com URL', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { video: { url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', title: 'Video de ejemplo' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    const iframe = screen.getByTitle('Video de ejemplo');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'https://www.youtube.com/embed/dQw4w9WgXcQ');
  });

  it('renders YouTube video embed for youtu.be short URL', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { video: { url: 'https://youtu.be/dQw4w9WgXcQ', title: 'Video corto' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    const iframe = screen.getByTitle('Video corto');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'https://www.youtube.com/embed/dQw4w9WgXcQ');
  });

  it('does not render video iframe for invalid URL', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { video: { url: 'not-a-valid-url', title: 'Video inválido' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.queryByTitle('Video inválido')).not.toBeInTheDocument();
  });

  it('does not render video iframe for youtube.com URL without v param', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { video: { url: 'https://www.youtube.com/watch', title: 'Video sin ID' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.queryByTitle('Video sin ID')).not.toBeInTheDocument();
  });

  it('renders image credit as plain text when no credit_url provided', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { image: { url: 'http://example.com/img.jpg', alt: 'Un animal', credit: 'Foto de Juan' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText('Foto de Juan')).toBeInTheDocument();
  });

  it('renders image credit as link when credit_url is provided', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        {
          image: {
            url: 'http://example.com/img.jpg',
            alt: 'Un animal',
            credit: 'Foto de Juan',
            credit_url: 'https://example.com/juan',
          },
        },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    const link = screen.getByRole('link', { name: 'Foto de Juan' });
    expect(link).toHaveAttribute('href', 'https://example.com/juan');
  });

  it('renders quote without author when author is omitted', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { quote: { text: 'Frase sin autor.' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByText(/Frase sin autor/)).toBeInTheDocument();
    expect(screen.queryByText(/^—/)).not.toBeInTheDocument();
  });

  it('renders image with empty alt when alt is not provided', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { image: { url: 'http://example.com/no-alt.jpg' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    const img = screen.getByTestId('section-image');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('alt', '');
  });

  it('renders YouTube video with default "Video" title when no title provided', () => {
    const contentJson = {
      intro: 'Intro',
      sections: [
        { video: { url: 'https://www.youtube.com/watch?v=abc123' } },
      ],
    };
    render(<BlogContentRenderer contentJson={contentJson} />);
    expect(screen.getByTitle('Video')).toBeInTheDocument();
  });
});


describe('BlogContentRenderer HTML safety', () => {
  it('discards executable markup', async () => {
    const { container } = render(<BlogContentRenderer contentHtml={
      '<p>Safe text</p><img src="/missing" onerror="window.__blogSecurityProbe=1">'
      + '<svg onload="window.__blogSecurityProbe=1"></svg><script>bad()</script>'
      + '<iframe src="/unsafe"></iframe><form><input></form>'
    } />);

    expect(await screen.findByText('Safe text')).toBeInTheDocument();
    expect(container.querySelector('[onerror], [onload], svg, script, iframe, form, input')).toBeNull();
  });

  it.each(['javascript:alert(1)', 'java&#10;script:alert(1)', 'data:text/html,unsafe', 'vbscript:bad()'])
  ('removes the unsafe link %s', async (href) => {
    render(<BlogContentRenderer contentHtml={`<a href="${href}">Unsafe link</a>`} />);

    expect(await screen.findByText('Unsafe link')).not.toHaveAttribute('href');
  });

  it('preserves editorial formatting', async () => {
    render(<BlogContentRenderer contentHtml={
      '<h2>Heading</h2><p><strong>Bold</strong><em>Emphasis</em></p>'
      + '<ul><li>Item</li></ul><figure><img src="https://example.com/photo.jpg" alt="Animal"><figcaption>Photo</figcaption></figure>'
      + '<table><tbody><tr><th scope="col">Column</th><td colspan="2">Cell</td></tr></tbody></table>'
      + '<a href="/es/animals#dogs" target="_blank" rel="opener">Animals</a>'
    } />);

    expect(await screen.findByRole('heading', { name: 'Heading' })).toBeInTheDocument();
    expect(screen.getByText('Bold').tagName).toBe('STRONG');
    expect(screen.getByText('Emphasis').tagName).toBe('EM');
    expect(screen.getByRole('listitem')).toHaveTextContent('Item');
    expect(screen.getByAltText('Animal')).toHaveAttribute('src', 'https://example.com/photo.jpg');
    expect(screen.getByRole('cell')).toHaveAttribute('colspan', '2');
    expect(screen.getByRole('link')).toHaveAttribute('href', '/es/animals#dogs');
    expect(screen.getByRole('link')).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('removes noneditorial attributes', async () => {
    render(<BlogContentRenderer contentHtml='<p style="color:red" class="secret" id="unsafe" data-probe="1" aria-label="probe">Plain</p>' />);

    const paragraph = await screen.findByText('Plain');
    expect(paragraph).toHaveTextContent('Plain');
    expect(paragraph.attributes).toHaveLength(0);
  });

  it('renders an empty HTML article on the server', () => {
    const markup = renderToString(<BlogContentRenderer contentHtml='<p>Untrusted server content</p>' />);

    expect(markup).not.toContain('Untrusted server content');
    expect(markup).toMatch(/<article[^>]*><\/article>/);
    expect(createPurifier).not.toHaveBeenCalled();
  });

  it('hydrates the empty server article without mismatches', async () => {
    const contentHtml = '<p>Hydrated content</p>';
    const host = document.createElement('div');
    host.innerHTML = renderToString(<BlogContentRenderer contentHtml={contentHtml} />);
    document.body.appendChild(host);
    const onRecoverableError = jest.fn();
    let root: ReturnType<typeof hydrateRoot> | undefined;

    await act(async () => {
      root = hydrateRoot(host, <BlogContentRenderer contentHtml={contentHtml} />, { onRecoverableError });
    });

    expect(host).toHaveTextContent('Hydrated content');
    expect(onRecoverableError).not.toHaveBeenCalled();
    await act(async () => { root?.unmount(); });
    host.remove();
  });

  it('never displays raw HTML while props change', async () => {
    const { container, rerender } = render(<BlogContentRenderer contentHtml='<p>Old article</p>' />);
    rerender(<BlogContentRenderer contentHtml='<p>New article</p><img src="/missing" onerror="bad()">' />);

    expect(container).not.toHaveTextContent('Old article');
    expect(container).not.toHaveTextContent('New article');
    expect(container.querySelector('[onerror]')).toBeNull();
    expect(await screen.findByText('New article')).toBeInTheDocument();
    expect(container).not.toHaveTextContent('Old article');
  });

  it('keeps the article empty when initialization fails', async () => {
    createPurifier.mockImplementationOnce(() => { throw new Error('Initialization failed'); });
    const { container } = render(<BlogContentRenderer contentHtml='<p>Must stay hidden</p>' />);

    await waitFor(() => expect(createPurifier).toHaveBeenCalledTimes(1));
    expect(container.querySelector('article')).toBeEmptyDOMElement();
  });

  it('keeps unsupported browsers from rendering unsanitized HTML', async () => {
    createPurifier.mockImplementationOnce(() => ({ isSupported: false } as ReturnType<typeof createDOMPurify>));
    const { container } = render(<BlogContentRenderer contentHtml='<p>Unsupported raw HTML</p>' />);

    await waitFor(() => expect(createPurifier).toHaveBeenCalledTimes(1));
    expect(container.querySelector('article')).toBeEmptyDOMElement();
  });

  it('prioritizes structured content over HTML', () => {
    render(<BlogContentRenderer contentJson={{ intro: 'Structured intro', sections: [] }} contentHtml='<p>Unused HTML</p>' />);

    expect(screen.getByRole('article')).toHaveTextContent('Structured intro');
    expect(screen.queryByText('Unused HTML')).not.toBeInTheDocument();
  });
});
