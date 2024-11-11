import { Editor } from "@/components/Editor";

import { ForwardedRef, forwardRef, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { SubmitHandler, useFieldArray } from "react-hook-form";
import { CallArgsCreate } from "@/types/types";
import { Label } from "@/components/ui/label";
import { LexicalEditor } from "lexical";
import {
  BaseEditorFormFields,
  EditorFormValues,
  useBaseEditorForm,
} from "@/utils/editor-form-utils";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { AddCardButton } from "@/components/AddCardButton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { $findErrorTemplateNodes } from "@/components/lexical/template-node";
import { $convertToMarkdownString } from "@lexical/markdown";
import { PLAYGROUND_TRANSFORMERS } from "@/components/lexical/markdown-transformers";
import { useNavigate } from "@tanstack/react-router";

interface CreateEditorFormProps {
  projectId: number;
}

type CreateEditorFormValues = EditorFormValues & {
  promptName: string;
  inputs: Record<string, string>[];
};
export const CreateEditorForm = ({ projectId }: CreateEditorFormProps) => {
  const navigate = useNavigate();
  const methods = useBaseEditorForm<CreateEditorFormValues>({});
  const { fields, append, remove } = useFieldArray<CreateEditorFormValues>({
    control: methods.control,
    name: "inputs",
  });
  const [editorErrors, setEditorErrors] = useState<string[]>([]);
  const editorRef = useRef<LexicalEditor>(null);
  const onSubmit: SubmitHandler<CreateEditorFormValues> = (
    data: EditorFormValues,
    event
  ) => {
    event?.preventDefault();
    if (!editorRef?.current) return;

    const editorErrors = $findErrorTemplateNodes(editorRef.current);
    if (editorErrors.length > 0) {
      setEditorErrors(
        editorErrors.map(
          (node) => `'${node.getValue()}' is not a function argument.`
        )
      );
      return;
    }
    const editorState = editorRef.current.getEditorState();
    editorState.read(() => {
      const markdown = $convertToMarkdownString(PLAYGROUND_TRANSFORMERS);
      data.prompt_template = markdown;
      // TODO: Mutate and navigate
      navigate({
        to: `/projects/${projectId}/llmFns/recommend_book/versions/1`,
      });
    });
  };
  return (
    <>
      <Form {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)}>
          <div className='button-group'>
            <Button type='submit' name='create-version'>
              Create version
            </Button>
          </div>
          <FormField
            control={methods.control}
            name='promptName'
            render={({ field }) => (
              <FormItem>
                <FormLabel>Prompt Function Name</FormLabel>
                <FormControl>
                  <Input {...field} placeholder='Enter prompt name' />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className='flex gap-4'>
            <div className='lexical form-group space-y-2'>
              <Label htmlFor='prompt-template'>Prompt Template</Label>
              <Editor inputs={[]} ref={editorRef} promptTemplate={""} />
              {editorErrors.length > 0 &&
                editorErrors.map((error, i) => (
                  <div key={i} className='text-red-500 text-sm mt-1'>
                    {error}
                  </div>
                ))}
            </div>
            <div className='flex flex-col gap-2'>
              <BaseEditorFormFields methods={methods} />
              <div className='space-y-2'>
                <FormLabel className='text-base'>{"Inputs"}</FormLabel>
                <div className='flex gap-4 overflow-x-auto pb-4'>
                  {fields.map((field, index) => (
                    <Card
                      key={field.id}
                      className='w-64 flex-shrink-0 relative'
                    >
                      <Button
                        type='button'
                        variant='ghost'
                        size='icon'
                        onClick={() => remove(index)}
                        className='h-6 w-6 absolute top-2 right-2 hover:bg-gray-100'
                      >
                        <X className='h-4 w-4' />
                      </Button>
                      <CardContent className='pt-6 space-y-4'>
                        <div className='w-full'>
                          <FormField
                            control={methods.control}
                            name={`inputs.${index}.key`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Args</FormLabel>
                                <FormControl>
                                  <Input placeholder='Args' {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                        <div className='w-full'>
                          <FormField
                            control={methods.control}
                            name={`inputs.${index}.value`}
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Type</FormLabel>
                                <FormControl>
                                  <Select
                                    value={field.value}
                                    onValueChange={field.onChange}
                                  >
                                    <SelectTrigger className='w-[200px]'>
                                      <SelectValue placeholder='Select modality' />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {["text", "image", "audio"].map(
                                        (name) => (
                                          <SelectItem key={name} value={name}>
                                            {name}
                                          </SelectItem>
                                        )
                                      )}
                                    </SelectContent>
                                  </Select>
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  <AddCardButton
                    onClick={() => append({ key: "", value: "" })}
                  />
                </div>
              </div>
            </div>
          </div>
        </form>
      </Form>
    </>
  );
};
