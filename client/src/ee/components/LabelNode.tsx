import { FailButton } from "@/components/FailButton";
import { SuccessButton } from "@/components/SuccessButton";
import { Label } from "@/types/types";
import { CustomNodeDefinition, CustomNodeProps } from "json-edit-react";
import { CircleCheck, CircleX } from "lucide-react";

export const LabelNode: React.FC<CustomNodeProps> = ({
  value,
  parentData,
  setValue,
  isEditing,
  setIsEditing,
  getStyles,
  nodeData,
}) => {
  const stringStyle = getStyles("string", nodeData);

  const exact = (parentData as { exact: boolean })?.exact;
  return isEditing ? (
    <div className="flex gap-2">
      <SuccessButton
        variant={value === Label.PASS ? "success" : "outline"}
        onClick={() => setValue(Label.PASS)}
      >
        Pass
      </SuccessButton>
      <FailButton
        variant={value === Label.FAIL ? "destructive" : "outline"}
        onClick={() => setValue(Label.FAIL)}
      >
        Fail
      </FailButton>
    </div>
  ) : (
    <div
      onDoubleClick={() => setIsEditing(true)}
      className="jer-value-string"
      style={stringStyle}
    >
      {value === Label.PASS && <CircleCheck color="#00a741" />}
      {value === Label.FAIL && <CircleX color="#e7000b" />}
      {!value && (
        <div>
          {exact ? (
            <i>Label will be automatically set</i>
          ) : (
            <i>Double click to label</i>
          )}
        </div>
      )}
    </div>
  );
};

// Definition for the custom node
export const labelNodeDefinition: CustomNodeDefinition = {
  // Condition to check if the value is a valid dual input JSON string
  condition: ({ key }) => {
    return key === "label";
  },

  element: LabelNode,
  showOnView: true,
  showOnEdit: true,
  name: "Label",
  showInTypesSelector: false,
};
