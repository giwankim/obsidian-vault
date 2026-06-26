import { defineConfig } from 'unocss'

// Slidev auto-merges this with its own UnoCSS preset.
// Demonstrates the Tailwind-style utility layer you can use inline in slides.
export default defineConfig({
  shortcuts: {
    // e.g. <div class="card"> … </div>
    card: 'p-4 rounded-lg bg-white/5 border border-white/10',
  },
})
