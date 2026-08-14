(function () {
    'use strict';

    function slugify(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    // ---- Rich text editor ----
    var editorEl = document.getElementById('editor');
    var quill = null;
    if (editorEl && window.Quill) {
        quill = new Quill('#editor', {
            theme: 'snow',
            placeholder: 'Write something...',
            modules: {
                toolbar: {
                    container: [
                        [{ header: [1, 2, 3, 4, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        ['blockquote', 'code-block'],
                        [{ list: 'ordered' }, { list: 'bullet' }],
                        ['link', 'image'],
                        ['clean'],
                    ],
                    handlers: {
                        image: function () {
                            var url = window.prompt('Image URL:');
                            if (url) {
                                var range = quill.getSelection(true);
                                quill.insertEmbed(range.index, 'image', url, 'user');
                            }
                        },
                    },
                },
            },
        });
    }

    var form = document.getElementById('page-form');
    if (form) {
        form.addEventListener('submit', function () {
            var hidden = document.getElementById('id_content_html');
            if (quill && hidden) {
                hidden.value = quill.root.innerHTML;
            }
        });
    }

    // ---- Slug auto-fill from title (create-page form only) ----
    var titleInput = document.getElementById('id_title');
    var slugInput = document.getElementById('id_slug');
    if (titleInput && slugInput) {
        var slugTouched = false;
        slugInput.addEventListener('input', function () { slugTouched = true; });
        titleInput.addEventListener('input', function () {
            if (!slugTouched) {
                slugInput.value = slugify(titleInput.value);
            }
        });
    }

    // ---- Classification picker live preview ----
    document.querySelectorAll('.classify-picker').forEach(function (picker) {
        var pickerId = picker.id.replace('classify-', '');
        var preview = document.getElementById('classify-preview-' + pickerId);
        if (!preview) { return; }

        function update() {
            var inputs = picker.querySelectorAll('.classify-input:checked');
            var parts = [];
            var color = '#6c757d';
            var first = true;
            inputs.forEach(function (input) {
                var label = input.closest('.classify-option');
                var code = label.textContent.split('—')[0].trim();
                parts.push(code);
                var dot = label.querySelector('.classify-dot');
                if (first && dot) {
                    color = dot.style.backgroundColor || color;
                }
                first = false;
            });
            preview.textContent = parts.length ? parts.join('//') : 'UNCLASSIFIED';
            preview.style.backgroundColor = parts.length ? color : '#6c757d';
        }

        picker.addEventListener('change', update);
        update();
    });

    // ---- Attachment upload panel toggle ----
    var attachToggle = document.getElementById('attach-toggle');
    var attachPanel = document.getElementById('attach-panel');
    if (attachToggle && attachPanel) {
        attachToggle.addEventListener('click', function () {
            attachPanel.classList.toggle('open');
        });
    }
})();
