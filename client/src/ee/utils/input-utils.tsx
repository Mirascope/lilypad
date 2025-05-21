import { AddCardButton } from "@/components/AddCardButton";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FileText, Image, Music, Upload, X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import {
  ControllerRenderProps,
  FieldPath,
  FieldValues,
  useFieldArray,
  useFormContext,
} from "react-hook-form";

// Define value types
export interface FormItemValue {
  type: "str" | "int" | "float" | "bool" | "bytes" | "list" | "dict";
  value: unknown;
}

export interface ListItemValue extends FormItemValue {
  id: string;
}

// Generic types for form components
interface FormInputWrapperProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> {
  name: TName;
  label?: string;
  description?: string;
  children: (field: ControllerRenderProps<TFieldValues, TName>) => React.ReactNode;
  containerClassName?: string;
  formItemClassName?: string;
}

interface TypedInputProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> {
  name: TName;
  type: "str" | "int" | "float" | "bool" | "bytes" | "list" | "dict";
  label?: string;
}

interface BaseInputProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
> {
  name: TName;
  label?: string;
}

// Base FormInput wrapper to reduce boilerplate
export const FormInputWrapper = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  label,
  description,
  children,
  containerClassName = "w-full",
  formItemClassName = "",
}: FormInputWrapperProps<TFieldValues, TName>) => {
  const { control } = useFormContext<TFieldValues>();
  return (
    <div className={containerClassName}>
      <FormField
        control={control}
        name={name}
        render={({ field }) => (
          <FormItem className={formItemClassName}>
            {label && <FormLabel>{label}</FormLabel>}
            {description && <FormDescription>{description}</FormDescription>}
            {children(field)}
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  );
};

// String Input
export const StringInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  label = "Value (str)",
}: BaseInputProps<TFieldValues, TName>) => {
  return (
    <FormInputWrapper name={name} label={label}>
      {(field) => (
        <FormControl>
          <Input
            {...field}
            placeholder="Enter text value"
            value={field.value ?? ""}
            onChange={field.onChange}
          />
        </FormControl>
      )}
    </FormInputWrapper>
  );
};

// Integer Input
export const IntegerInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  label = "Value (int)",
}: BaseInputProps<TFieldValues, TName>) => {
  return (
    <FormInputWrapper name={name} label={label}>
      {(field) => (
        <FormControl>
          <Input
            {...field}
            type="number"
            step="1"
            placeholder="Enter integer value"
            value={field.value ?? ""}
            onChange={(e) => {
              const value = e.target.value === "" ? "" : parseInt(e.target.value, 10);
              field.onChange(value);
            }}
          />
        </FormControl>
      )}
    </FormInputWrapper>
  );
};

// Float Input
export const FloatInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  label = "Value (float)",
}: BaseInputProps<TFieldValues, TName>) => {
  return (
    <FormInputWrapper name={name} label={label}>
      {(field) => (
        <FormControl>
          <Input
            {...field}
            type="number"
            step="0.01"
            placeholder="Enter float value"
            value={field.value ?? ""}
            onChange={(e) => {
              const value = e.target.value === "" ? "" : parseFloat(e.target.value);
              field.onChange(value);
            }}
          />
        </FormControl>
      )}
    </FormInputWrapper>
  );
};

// Boolean Input
export const BooleanInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  label = "Value (bool)",
}: BaseInputProps<TFieldValues, TName>) => {
  return (
    <FormInputWrapper name={name} label={label}>
      {(field) => (
        <FormControl>
          <div>
            <Checkbox
              className="h-6 w-6"
              checked={!!field.value}
              onCheckedChange={field.onChange}
            />
          </div>
        </FormControl>
      )}
    </FormInputWrapper>
  );
};

// Bytes Input - handles raw bytes input or file uploads (images, audio, etc.)
export const BytesInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  label = "Value (bytes)",
}: BaseInputProps<TFieldValues, TName>) => {
  const [inputMode, setInputMode] = useState<"text" | "file">("text");
  const [fileType, setFileType] = useState<"image" | "audio" | "other">("other");
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>,
    onChange: (...event: any[]) => void
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Determine file type for preview
    if (file.type.startsWith("image/")) {
      setFileType("image");
    } else if (file.type.startsWith("audio/")) {
      setFileType("audio");
    } else {
      setFileType("other");
    }

    try {
      // Read file as base64
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remove the data:*/*;base64, prefix to get just the encoded content
        const base64Data = result.split(",")[1];
        // Set the value in the form
        onChange(base64Data);

        // Keep the full data URL for preview
        setPreview(result);
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error("Error reading file:", error);
    }
  };

  const handleTextInput = (
    e: React.ChangeEvent<HTMLTextAreaElement>,
    onChange: (...event: any[]) => void
  ) => {
    onChange(e.target.value);
    setPreview(null);
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  const renderPreview = (value: any) => {
    if (!preview) return null;

    if (fileType === "image") {
      return (
        <div className="mt-2">
          <p className="mb-1 text-sm text-gray-500">Image Preview:</p>
          <img
            src={preview}
            alt="Preview"
            className="max-h-40 max-w-full rounded border object-contain"
          />
        </div>
      );
    } else if (fileType === "audio") {
      return (
        <div className="mt-2">
          <p className="mb-1 text-sm text-gray-500">Audio Preview:</p>
          <audio controls className="w-full">
            <source src={preview} />
            Your browser does not support the audio element.
          </audio>
        </div>
      );
    } else if (value) {
      return (
        <div className="mt-2 flex items-center text-sm text-gray-500">
          <FileText className="mr-1 h-4 w-4" />
          <span>File loaded ({Math.round((value.length * 3) / 4 / 1024)} KB)</span>
        </div>
      );
    }

    return null;
  };

  return (
    <FormInputWrapper name={name} label={label}>
      {(field) => (
        <FormControl>
          <div className="space-y-2">
            <div className="mb-2 flex gap-2">
              <Button
                type="button"
                variant={inputMode === "text" ? "default" : "outline"}
                onClick={() => setInputMode("text")}
                size="sm"
                className="flex-1"
              >
                Text Input
              </Button>
              <Button
                type="button"
                variant={inputMode === "file" ? "default" : "outline"}
                onClick={() => setInputMode("file")}
                size="sm"
                className="flex-1"
              >
                File Upload
              </Button>
            </div>

            {inputMode === "text" ? (
              <textarea
                className="border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Enter base64 encoded bytes"
                value={field.value || ""}
                onChange={(e) => handleTextInput(e, field.onChange)}
              />
            ) : (
              <div className="space-y-2">
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={triggerFileSelect}
                    className="flex w-full items-center justify-center gap-1"
                  >
                    <Image className="h-4 w-4" />
                    <span>Image</span>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={triggerFileSelect}
                    className="flex w-full items-center justify-center gap-1"
                  >
                    <Music className="h-4 w-4" />
                    <span>Audio</span>
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={triggerFileSelect}
                    className="flex w-full items-center justify-center gap-1"
                  >
                    <FileText className="h-4 w-4" />
                    <span>Other File</span>
                  </Button>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={(e) => void handleFileChange(e, field.onChange)}
                  className="hidden"
                  accept="*/*"
                />
                <div
                  className="hover:border-primary flex w-full cursor-pointer items-center justify-center rounded-md border-2 border-dashed p-6"
                  onClick={triggerFileSelect}
                >
                  <div className="flex flex-col items-center">
                    <Upload className="h-8 w-8 text-gray-400" />
                    <p className="mt-2 text-sm text-gray-500">Click to upload or drag and drop</p>
                    <p className="text-xs text-gray-400">Any file type supported</p>
                  </div>
                </div>
              </div>
            )}

            {renderPreview(field.value)}

            {field.value && inputMode === "text" && (
              <div className="text-xs text-gray-500">
                {field.value.length} characters ({Math.round((field.value.length * 3) / 4 / 1024)}{" "}
                KB approx)
              </div>
            )}
          </div>
        </FormControl>
      )}
    </FormInputWrapper>
  );
};

const pythonTypes = ["str", "int", "float", "bool", "bytes", "list", "dict"];

// List Input
export const ListInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
}: BaseInputProps<TFieldValues, TName>) => {
  const { control } = useFormContext<TFieldValues>();
  const { fields, append, remove } = useFieldArray({
    control,
    name: name as unknown as any,
  });
  const methods = useFormContext<TFieldValues>();
  return (
    <FormItem className="w-full">
      <FormControl>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-4 pb-4">
            {fields.map((field, index) => {
              const type =
                methods.watch(
                  `${String(name)}.${index}.type` as unknown as FieldPath<TFieldValues>
                ) || "str";
              return (
                <Card key={field.id} className="relative w-full shrink-0">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(index)}
                    className="absolute top-2 right-2 h-6 w-6 hover:bg-gray-100"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                  <CardContent className="space-y-4 pt-6">
                    <div className="flex w-full gap-2">
                      <FormField
                        control={control}
                        // Using type assertion to handle nested paths
                        name={`${name}.${index}.type` as unknown as FieldPath<TFieldValues>}
                        render={({ field }) => {
                          return (
                            <FormItem>
                              <FormLabel>Type</FormLabel>
                              <FormControl>
                                <Select value={field.value || "str"} onValueChange={field.onChange}>
                                  <SelectTrigger className="w-full">
                                    <SelectValue placeholder="Select input type" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {pythonTypes.map((type) => (
                                      <SelectItem key={type} value={type}>
                                        {type}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          );
                        }}
                      />
                      <TypedInput
                        name={
                          `${String(name)}.${index}.value` as unknown as FieldPath<TFieldValues>
                        }
                        type={type as any}
                        label={`Value (list item ${index + 1} ${type})`}
                      />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            <AddCardButton
              className="h-[116px] w-full"
              onClick={() => append({ type: "str", value: "" } as unknown as any)}
            />
          </div>
        </div>
      </FormControl>
      <FormMessage />
    </FormItem>
  );
};

// Object Input
export const ObjectInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  label = "Value (dict)",
}: BaseInputProps<TFieldValues, TName>) => {
  const methods = useFormContext<TFieldValues>();
  const objectValue = methods.watch(name) || {};

  // Convert flat object to structured format with type and value
  const getStructuredEntries = () => {
    const result: { key: string; type: string; value: unknown }[] = [];
    Object.entries(objectValue).forEach(([key, val]) => {
      // If value is already in our structured format
      if (val && typeof val === "object" && "type" in val && "value" in val) {
        result.push({ key, type: val.type as string, value: val.value });
      } else {
        // Determine type based on value
        let type = "str";
        if (Array.isArray(val)) type = "list";
        else if (val !== null && typeof val === "object") type = "dict";
        else if (typeof val === "boolean") type = "bool";
        else if (typeof val === "number") {
          type = Number.isInteger(val) ? "int" : "float";
        }

        result.push({ key, type, value: val });
      }
    });
    return result;
  };

  const entries = getStructuredEntries();

  const handleAddProperty = () => {
    const currentObj = methods.getValues(name) || {};
    const newKey = `key${Object.keys(currentObj).length + 1}`;
    methods.setValue(
      name as FieldPath<TFieldValues>,
      {
        ...currentObj,
        [newKey]: { type: "str", value: "" },
      } as any
    );
  };

  const handleRemoveProperty = (key: string) => {
    const currentObj = { ...methods.getValues(name) };
    delete currentObj[key];
    methods.setValue(name, currentObj);
  };

  const handleKeyChange = (oldKey: string, newKey: string) => {
    const currentObj = { ...methods.getValues(name) };
    const value = currentObj[oldKey];
    delete currentObj[oldKey];
    currentObj[newKey] = value;
    methods.setValue(name, currentObj);
  };

  const handleTypeChange = (key: string, newType: string) => {
    const currentObj = { ...methods.getValues(name) };

    // Reset value based on new type
    let newValue: unknown = "";
    if (newType === "str") newValue = "";
    else if (newType === "int") newValue = 0;
    else if (newType === "float") newValue = 0.0;
    else if (newType === "bool") newValue = false;
    else if (newType === "bytes") newValue = "";
    else if (newType === "list") newValue = [];
    else if (newType === "dict") newValue = {};

    currentObj[key] = { type: newType, value: newValue };
    methods.setValue(name, currentObj);
  };

  const handleValueChange = (key: string, newValue: unknown) => {
    const currentObj = { ...methods.getValues(name) };
    if (currentObj[key] && typeof currentObj[key] === "object") {
      currentObj[key] = {
        ...currentObj[key],
        value: newValue,
      };
    } else {
      currentObj[key] = { type: "str", value: newValue };
    }
    methods.setValue(name, currentObj);
  };

  return (
    <FormInputWrapper name={name} label={label}>
      {(_field) => (
        <div className="space-y-4 rounded-md border p-4">
          {entries.map(({ key, type, value }, entryIndex) => {
            const valueLabel = `Value (${type})`;
            return (
              <Card key={entryIndex} className="relative w-full shrink-0">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => handleRemoveProperty(key)}
                  className="absolute top-2 right-2 h-6 w-6 hover:bg-gray-100"
                >
                  <X className="h-4 w-4" />
                </Button>
                <CardContent className="space-y-4 pt-6">
                  <FormItem>
                    <FormLabel>Key</FormLabel>
                    <Input
                      value={key}
                      onChange={(e) => handleKeyChange(key, e.target.value)}
                      placeholder="Key"
                      className="w-full"
                    />
                  </FormItem>
                  <div className="flex gap-2">
                    <FormItem>
                      <FormLabel>Type</FormLabel>
                      <Select
                        value={type || "str"}
                        onValueChange={(newType) => handleTypeChange(key, newType)}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          {pythonTypes.map((t) => (
                            <SelectItem key={t} value={t}>
                              {t}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormItem>
                    <FormItem className="w-full">
                      <FormLabel>{valueLabel}</FormLabel>
                      {type === "str" && (
                        <Input
                          value={(value as any) ?? ""}
                          onChange={(e) => handleValueChange(key, e.target.value)}
                          placeholder="String value"
                        />
                      )}
                      {type === "int" && (
                        <Input
                          type="number"
                          step="1"
                          value={(value as any) ?? ""}
                          onChange={(e) => {
                            const val = e.target.value === "" ? "" : parseInt(e.target.value, 10);
                            handleValueChange(key, val);
                          }}
                          placeholder="Integer value"
                        />
                      )}
                      {type === "float" && (
                        <Input
                          type="number"
                          step="0.01"
                          value={(value as any) ?? ""}
                          onChange={(e) => {
                            const val = e.target.value === "" ? "" : parseFloat(e.target.value);
                            handleValueChange(key, val);
                          }}
                          placeholder="Float value"
                        />
                      )}
                      {type === "bool" && (
                        <div className="items-center justify-end">
                          <Checkbox
                            className="h-6 w-6"
                            checked={!!value}
                            onCheckedChange={(checked) => handleValueChange(key, !!checked)}
                          />
                        </div>
                      )}
                      {type === "list" && (
                        <ListInput
                          name={
                            `${String(name)}.${key}.value` as unknown as FieldPath<TFieldValues>
                          }
                          label=""
                        />
                      )}
                      {type === "dict" && (
                        <ObjectInput
                          name={
                            `${String(name)}.${key}.value` as unknown as FieldPath<TFieldValues>
                          }
                          label=""
                        />
                      )}
                    </FormItem>
                  </div>
                </CardContent>
              </Card>
            );
          })}
          <Button type="button" variant="outline" onClick={handleAddProperty} className="w-full">
            Add Property
          </Button>
        </div>
      )}
    </FormInputWrapper>
  );
};

// TypedInput component that selects the appropriate input based on type
export const TypedInput = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  name,
  type,
  label,
}: TypedInputProps<TFieldValues, TName>) => {
  const methods = useFormContext<TFieldValues>();
  useEffect(() => {
    let newValue: any = "";
    if (type === "str") newValue = "";
    else if (type === "int") newValue = 0;
    else if (type === "float") newValue = 0.0;
    else if (type === "bool") newValue = false;
    else if (type === "bytes") newValue = "";
    else if (type === "list") newValue = [];
    else if (type === "dict") newValue = {};
    methods?.setValue(name, newValue);
  }, [type]);
  const labelWithType = label ?? `Value (${type})`;
  switch (type) {
    case "str":
      return <StringInput name={name} label={labelWithType} />;
    case "int":
      return <IntegerInput name={name} label={labelWithType} />;
    case "float":
      return <FloatInput name={name} label={labelWithType} />;
    case "bool":
      return <BooleanInput name={name} label={labelWithType} />;
    case "bytes":
      return <BytesInput name={name} label={labelWithType} />;
    case "list":
      return <ListInput name={name} label={labelWithType} />;
    case "dict":
      return <ObjectInput name={name} label={labelWithType} />;
    default:
      return <StringInput name={name} label={labelWithType} />;
  }
};

export interface NestedFormItemValue {
  [key: string]: FormItemValue | NestedFormItemValue;
}

type NestedArray = NestedValue[];

type NestedValue = FormItemValue | NestedFormItemValue | NestedArray;

type SimplifiedValue = unknown;

/**
 * Simplifies a FormItemValue by extracting just the value while handling nested structures
 */
export const simplifyFormItem = (formItem: FormItemValue): SimplifiedValue => {
  switch (formItem.type) {
    case "dict":
      return simplifyNested(formItem.value as Record<string, any>);
    case "list":
      return Array.isArray(formItem.value)
        ? formItem.value.map((item) => simplifyNested(item))
        : [];
    case "bytes":
      // For bytes, we ensure the value is a proper string and let it pass through
      return typeof formItem.value === "string" ? formItem.value : "";
    default:
      return formItem.value;
  }
};

/**
 * Simplifies a nested structure by recursively processing each value
 */
export const simplifyNested = (data: any): SimplifiedValue => {
  if (typeof data !== "object" || data === null) {
    return data;
  }

  // Handle arrays
  if (Array.isArray(data)) {
    return data.map((item) => simplifyNested(item));
  }

  // Check if the object is a FormItemValue
  if ("type" in data && "value" in data) {
    return simplifyFormItem(data as FormItemValue);
  }

  // For regular objects, process each property recursively
  const result: Record<string, SimplifiedValue> = {};
  for (const key in data) {
    result[key] = simplifyNested(data[key]);
  }

  return result;
};
