import { useTheme } from "@/src/components/theme-provider";
import ReactJsonView, { JsonViewProps } from "@uiw/react-json-view";
import { vscodeTheme } from "@uiw/react-json-view/vscode";

export const JsonView = <T extends object>(props: JsonViewProps<T>) => {
  const { theme } = useTheme();

  return (
    <ReactJsonView
      className="h-full w-full overflow-auto rounded-md p-2 shadow-sm"
      style={{
        ...(theme === "dark" && vscodeTheme),
        ...props.style,
      }}
      {...(props as any)}
    />
  );
};
