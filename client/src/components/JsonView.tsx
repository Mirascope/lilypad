import { useTheme } from "@/components/ThemeProvider";
import ReactJsonView, { JsonViewProps } from "@uiw/react-json-view";
import { vscodeTheme } from "@uiw/react-json-view/vscode";

export const JsonView = <T extends object>(props: JsonViewProps<T>) => {
  const { theme } = useTheme();

  return (
    <ReactJsonView
      className="p-2 rounded-md h-full w-full overflow-auto shadow-sm"
      style={{
        ...(theme === "dark" && vscodeTheme),
        ...props.style,
      }}
      {...(props as any)}
    />
  );
};
