import React, { useState, useEffect } from "react";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { $getSelection, $setSelection } from "lexical";

function CodeBlockComponent({ nodeKey }) {
  const [editor] = useLexicalComposerContext();
  const [language, setLanguage] = useState("javascript");

  useEffect(() => {
    editor.getEditorState().read(() => {
      const node = editor.getElementByKey(nodeKey);
      if (node) {
        setLanguage(node.getLanguage());
      }
    });
  }, [editor, nodeKey]);

  const onLanguageChange = (e) => {
    const newLanguage = e.target.value;
    setLanguage(newLanguage);
    editor.update(() => {
      const node = editor.getElementByKey(nodeKey);
      if (node) {
        node.setLanguage(newLanguage);
      }
    });
  };

  return (
    <div className='code-block'>
      <select
        className='language-selector'
        value={language}
        onChange={onLanguageChange}
      >
        <option value='javascript'>JavaScript</option>
        <option value='python'>Python</option>
        {/* Add more language options as needed */}
      </select>
      <pre>{/* Render code content here */}</pre>
    </div>
  );
}

export default CodeBlockComponent;
