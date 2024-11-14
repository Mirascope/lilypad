import { Editor } from "@/components/Editor";

import { ForwardedRef, forwardRef } from "react";
import { Button } from "@/components/ui/button";
import { FormProvider, SubmitHandler } from "react-hook-form";
import { FunctionPublic, VersionPublic } from "@/types/types";
import { Label } from "@/components/ui/label";
import { LexicalEditor } from "lexical";
import {
  BaseEditorFormFields,
  EditorFormValues,
  useBaseEditorForm,
} from "@/utils/editor-form-utils";

interface EditorFormProps {
  latestVersion?: VersionPublic | null;
  llmFunction?: FunctionPublic;
  onSubmit: SubmitHandler<EditorFormValues>;
  editorErrors: string[];
  formButtons?: React.ReactNode[];
}

export const EditorForm = forwardRef(
  (
    {
      latestVersion,
      llmFunction,
      onSubmit,
      editorErrors,
      formButtons,
    }: EditorFormProps,
    ref: ForwardedRef<LexicalEditor>
  ) => {
    const inputs = llmFunction?.arg_types
      ? llmFunction && Object.keys(llmFunction.arg_types)
      : [];
    const methods = useBaseEditorForm<EditorFormValues>({ latestVersion });
    return (
      <div className='flex flex-col gap-2'>
        <FormProvider {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)}>
            <div className='flex gap-2'>
              <div className='lexical form-group'>
                <Label htmlFor='prompt-template'>Prompt Template</Label>
                <Editor
                  inputs={inputs}
                  ref={ref}
                  promptTemplate={
                    (latestVersion &&
                      latestVersion.prompt &&
                      latestVersion.prompt.template) ||
                    ""
                  }
                />
                {editorErrors.length > 0 &&
                  editorErrors.map((error, i) => (
                    <div key={i} className='text-red-500 text-sm mt-1'>
                      {error}
                    </div>
                  ))}
              </div>
              <BaseEditorFormFields methods={methods} />
            </div>
            <div className='button-group'>
              <Button type='submit' name='create-version'>
                Create version
              </Button>
              {formButtons && formButtons.map((button) => button)}
            </div>
          </form>
        </FormProvider>
      </div>
    );
  }
);
