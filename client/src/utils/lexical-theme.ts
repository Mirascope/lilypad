import { EditorThemeClasses } from "lexical";

const exampleTheme: EditorThemeClasses = {
  ltr: "ltr",
  rtl: "rtl",
  placeholder: "editor-placeholder",
  paragraph: "editor-paragraph",
  quote: "editor-quote",
  role: "editor-role",
  heading: {
    h1: "editor-heading-h1",
    h2: "editor-heading-h2",
    h3: "editor-heading-h3",
    h4: "editor-heading-h4",
    h5: "editor-heading-h5",
  },
  list: {
    nested: {
      listitem: "editor-nested-listitem",
    },
    ol: "editor-list-ol",
    olDepth: ["editor-ol1", "editor-ol2", "editor-ol3", "editor-ol4", "editor-ol5"],
    ul: "editor-list-ul",
    listitem: "editor-listitem",
  },
  image: "editor-image",
  link: "editor-link",
  text: {
    bold: "editor-text-bold",
    italic: "editor-text-italic",
    overflowed: "editor-text-overflowed",
    hashtag: "editor-text-hashtag",
    underline: "editor-text-underline",
    strikethrough: "editor-text-strikethrough",
    underlineStrikethrough: "editor-text-underlineStrikethrough",
    code: "editor-text-code not-prose",
  },
  code: "editor-code not-prose",
};

export default exampleTheme;
