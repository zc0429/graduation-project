<script setup lang="ts">
import { computed, watch } from 'vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Subscript from '@tiptap/extension-subscript'
import Superscript from '@tiptap/extension-superscript'
import { questionHtml, questionText } from '@/utils/question-content'

const props = withDefaults(defineProps<{ modelValue: string; label?: string; disabled?: boolean }>(), {
  label: '题干', disabled: false,
})
const emit = defineEmits<{ 'update:modelValue': [value: string]; blur: [] }>()
const editor = useEditor({
  content: questionHtml(props.modelValue),
  extensions: [StarterKit.configure({
    heading: false, blockquote: false, code: false, codeBlock: false,
    horizontalRule: false, link: false, underline: {},
  }), Subscript, Superscript],
  editorProps: { attributes: {
    role: 'textbox', 'aria-label': props.label, 'aria-multiline': 'true',
    'data-testid': 'question-editor',
  } },
  editable: !props.disabled,
  onUpdate: ({ editor: current }) => emit('update:modelValue', questionHtml(current.getHTML())),
  onBlur: () => emit('blur'),
})
const length = computed(() => questionText(props.modelValue).length)
const tools = computed(() => editor.value ? [
  { label: '加粗', active: editor.value.isActive('bold'), run: () => editor.value?.chain().focus().toggleBold().run() },
  { label: '斜体', active: editor.value.isActive('italic'), run: () => editor.value?.chain().focus().toggleItalic().run() },
  { label: '下划线', active: editor.value.isActive('underline'), run: () => editor.value?.chain().focus().toggleUnderline().run() },
  { label: '删除线', active: editor.value.isActive('strike'), run: () => editor.value?.chain().focus().toggleStrike().run() },
  { label: '无序列表', active: editor.value.isActive('bulletList'), run: () => editor.value?.chain().focus().toggleBulletList().run() },
  { label: '有序列表', active: editor.value.isActive('orderedList'), run: () => editor.value?.chain().focus().toggleOrderedList().run() },
  { label: '上标', active: editor.value.isActive('superscript'), run: () => editor.value?.chain().focus().unsetSubscript().toggleSuperscript().run() },
  { label: '下标', active: editor.value.isActive('subscript'), run: () => editor.value?.chain().focus().unsetSuperscript().toggleSubscript().run() },
] : [])
watch(() => props.modelValue, (value) => {
  if (editor.value && questionHtml(editor.value.getHTML()) !== questionHtml(value)) {
    editor.value.commands.setContent(questionHtml(value), { emitUpdate: false })
  }
})
watch(() => props.disabled, (disabled) => editor.value?.setEditable(!disabled))
</script>

<template>
  <div class="question-editor" :class="{ 'is-invalid': length > 2000 }">
    <div class="question-editor-tools" role="toolbar" aria-label="文字格式">
      <button v-for="tool in tools" :key="tool.label" type="button" :disabled="disabled"
        :aria-label="tool.label" :aria-pressed="tool.active" @click="tool.run">{{ tool.label }}</button>
      <button type="button" :disabled="disabled" @click="editor?.chain().focus().unsetAllMarks().clearNodes().run()">清除格式</button>
    </div>
    <EditorContent :editor="editor" />
    <p class="question-editor-hint">Enter 分段，Shift+Enter 换行 · {{ length }} / 2000 字</p>
  </div>
</template>

<style scoped>
.question-editor { width:100%; border:1px solid var(--el-border-color); border-radius:7px; background:var(--paper-bright,#fff); }
.question-editor:focus-within { border-color:var(--jade,#397766); }
.question-editor.is-invalid { border-color:var(--el-color-danger); }
.question-editor-tools { display:flex; flex-wrap:wrap; gap:4px; padding:8px; border-bottom:1px solid var(--el-border-color); }
.question-editor-tools button { padding:4px 7px; border:1px solid transparent; border-radius:4px; background:transparent; color:var(--ink,#25313a); font:inherit; font-size:12px; cursor:pointer; }
.question-editor-tools button[aria-pressed=true] { background:var(--jade-pale,#e8f2eb); border-color:var(--jade,#397766); }
.question-editor-tools button:focus-visible { outline:2px solid var(--jade,#397766); }
.question-editor :deep(.tiptap) { min-height:150px; max-height:400px; overflow:auto; padding:12px; outline:none; line-height:1.8; overflow-wrap:anywhere; }
.question-editor :deep(p) { margin:0 0 .5em; }
.question-editor :deep(ul), .question-editor :deep(ol) { padding-left:1.6em; }
.question-editor-hint { margin:0; padding:4px 10px; color:var(--ink-faint,#666); font-size:11px; }
</style>
