---
name: blog-visual-storyteller
description: Design and generate technical blog illustrations, SVG diagrams, memes, architecture visualizations, and MDX ImageCaption components using the project's visual guidelines.
---

# Blog Visual Storyteller

## Role

Act as a technical information designer.

Transform complex engineering explanations into simple, memorable visuals.

## Mandatory Guidelines

Read the blog image guidelines in CLAUDE.md before creating images.

All blog illustrations must:

- Be SVG files.
- Live under public/blog/<post-slug>/.
- Use 800px standard width.
- Use system sans-serif fonts.
- Have a white root background.
- Follow the project's neutral color palette.
- Be embedded through ImageCaption in MDX.

## Visual Selection

For every proposed visual, first determine:

1. What single idea should the reader understand?
2. Which section needs visual support?
3. Would a meme communicate this better than a conventional diagram?
4. What is the simplest possible visual?

First invent a format specific to the post's story. Check which formats recent posts in content/blog/ used, and don't repeat one from the last few posts.

If no story-specific format works, use one of these templates:

- Tier list: rankings and comparisons.
- Iceberg: hidden complexity. Last resort, because it's overused on this blog.
- Survival scoreboard: resource constraints.
- Before/After: optimization results.
- Architecture diagram: system topology.


## Generation Process

1. Analyze the approved article outline.
2. Identify sections that genuinely benefit from visuals.
3. Propose the visual concept for each section.
4. Explain the intended message in one sentence.
5. Generate the SVG.
6. Verify dimensions, colors, text length, and readability.
7. Add the corresponding ImageCaption MDX component.

Do not create decorative images without explanatory value.

## Quality Check

Before finishing:

- Validate SVG syntax.
- Ensure all text fits.
- Check that the image communicates one idea.
- Check width and height against the viewBox.
- Ensure ImageCaption references the correct path.
