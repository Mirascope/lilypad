import React, {Dispatch, SetStateAction, Suspense, useCallback, useEffect, useRef, useState} from "react"; // Import necessary hooks
import {Editor} from "@/ee/components/Editor";
import {AddCardButton} from "@/components/AddCardButton";
import {NotFound} from "@/components/NotFound";
import {Button} from "@/components/ui/button";
import {Card, CardContent} from "@/components/ui/card";
import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage,} from "@/components/ui/form";
import {Input} from "@/components/ui/input";
import {Select, SelectContent, SelectItem, SelectTrigger, SelectValue,} from "@/components/ui/select";
import {
    Sheet,
    SheetClose,
    SheetContent,
    SheetFooter,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import {Tooltip, TooltipContent, TooltipTrigger,} from "@/components/ui/tooltip";
import {EditorParameters, usePlaygroundContainer,} from "@/ee/hooks/use-playground";
import {TypedInput} from "@/ee/utils/input-utils";
import {FunctionPublic, PlaygroundErrorDetail} from "@/types/types";
import {BaseEditorFormFields, validateInputs} from "@/utils/playground-utils";
import {AlertTriangle, GripVertical, X} from "lucide-react";
import {SubmitHandler, useFieldArray, useFormContext} from "react-hook-form";
import {useSuspenseQuery} from "@tanstack/react-query";
import {spanQueryOptions} from "@/utils/spans";
import {LilypadPanel} from "@/components/LilypadPanel";
import CardSkeleton from "@/components/CardSkeleton";


const PlaygroundError = ({error}: { error: PlaygroundErrorDetail }) => {
    return (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 my-4">
            <div className="flex items-start">
                <div className="flex-shrink-0">
                    <AlertTriangle className="h-5 w-5 text-red-500"/>
                </div>
                <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                        {typeof error.type === 'string' ? error.type.replace(/_/g, ' ') : 'Error'}
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                        <p>{error.reason}</p>
                        {error.details && (
                            <details className="mt-2">
                                <summary className="cursor-pointer text-xs font-medium">Technical details</summary>
                                <pre
                                    className="mt-2 text-xs p-2 bg-red-100 rounded overflow-auto whitespace-pre-wrap break-all">
                      {typeof error.details === 'object' ? JSON.stringify(error.details, null, 2) : error.details}
                    </pre>
                            </details>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

const ExecutedSpanDetailPanel = ({spanUuid}: { spanUuid: string }) => {
    const {data: span} = useSuspenseQuery(spanQueryOptions(spanUuid));
    return (
        <div className='flex flex-col gap-4 h-full overflow-y-auto'>
            <div className='p-4 border rounded-md overflow-auto flex-1'>
                <h2 className='text-lg font-semibold mb-4'>Run Details</h2>
                <LilypadPanel spanUuid={span.uuid}/>
            </div>
        </div>
    );
};


export const Playground = ({
   version,
   error,
   isCompare,
   showRunButton,
   playgroundContainer,
}: {
    version: FunctionPublic | null;
    error?: PlaygroundErrorDetail | null;
    isCompare?: boolean;
    showRunButton?: boolean;
    playgroundContainer?: ReturnType<typeof usePlaygroundContainer>;
}) => {
    const defaultContainer = usePlaygroundContainer({
        version,
        isCompare: isCompare ?? false,
    });

    const {
        methods,
        editorRef,
        inputs,
        inputValues,
        editorErrors,
        openInputDrawer,
        setOpenInputDrawer,
        doesProviderExist,
        isRunLoading,
        onSubmit,
        handleReset,
        projectUuid,
        isDisabled,
        executedSpanUuid,
        error: containerError,
    } = playgroundContainer ?? defaultContainer;

    const displayError = error ?? containerError;
    const showRightPanel = Boolean(executedSpanUuid ?? displayError);

    const [isResizing, setIsResizing] = useState(false);
    const [rightPanelWidthPercent, setRightPanelWidthPercent] = useState<number | null>(null);
    const containerRef = useRef<HTMLDivElement>(null); // Ref for the main container
    const leftPanelRef = useRef<HTMLDivElement>(null); // Ref for the left panel
    const rightPanelRef = useRef<HTMLDivElement>(null); // Ref for the right panel
    const MIN_PANEL_WIDTH_PERCENT = 20; // Minimum width for panels during resize

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';
    };

    const handleMouseUp = useCallback(() => {
        if (isResizing) {
            setIsResizing(false);
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
        }
    }, [isResizing]);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizing || !containerRef.current || !leftPanelRef.current || !rightPanelRef.current || rightPanelWidthPercent === null) {
            return;
        }

        const containerRect = containerRef.current.getBoundingClientRect();
        const containerWidth = containerRect.width;
        const mouseXRelative = e.clientX - containerRect.left;

        let newLeftWidthPercent = (mouseXRelative / containerWidth) * 100;

        if (newLeftWidthPercent < MIN_PANEL_WIDTH_PERCENT) {
            newLeftWidthPercent = MIN_PANEL_WIDTH_PERCENT;
        }
        const maxLeftWidthPercent = 100 - MIN_PANEL_WIDTH_PERCENT;
        if (newLeftWidthPercent > maxLeftWidthPercent) {
            newLeftWidthPercent = maxLeftWidthPercent;
        }

        const newRightWidthPercent = 100 - newLeftWidthPercent;

        setRightPanelWidthPercent(newRightWidthPercent);


    }, [isResizing, containerRef, leftPanelRef, rightPanelRef, rightPanelWidthPercent]);

    useEffect(() => {
        if (isResizing) {
            window.addEventListener("mousemove", handleMouseMove);
            window.addEventListener("mouseup", handleMouseUp);
        } else {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
        }

        return () => {
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
            if (document.body.style.cursor === 'col-resize') {
                document.body.style.cursor = '';
            }
            if (document.body.style.userSelect === 'none') {
                document.body.style.userSelect = '';
            }
        };
    }, [isResizing, handleMouseMove, handleMouseUp]);

    useEffect(() => {
        if (showRightPanel) {
            if (rightPanelWidthPercent === null) {
                setRightPanelWidthPercent(50); // Default to 50% width when shown
            }
        } else {
            setRightPanelWidthPercent(null);
        }
    }, [showRightPanel]); // Only re-run when showRightPanel changes


    if (!projectUuid) return <NotFound/>;

    const renderRunButton = () => {
        return (
            <Tooltip>
                <TooltipTrigger asChild>
          <span>
            <Button
                name='run'
                loading={isRunLoading}
                disabled={!doesProviderExist || isDisabled}
                className='hover:bg-green-700 text-white font-medium'
            >
              Run
            </Button>
          </span>
                </TooltipTrigger>
                {/* ... TooltipContent ... */}
                <TooltipContent className='bg-gray-700 text-white'>
                    <p className='max-w-xs break-words'>
                        {doesProviderExist ? (
                            "Run the playground with the selected provider."
                        ) : (
                            <span>You need to add an API key to run the playground.</span>
                        )}
                    </p>
                </TooltipContent>
            </Tooltip>
        );
    };

    const leftFlexBasis = rightPanelWidthPercent === null ? '100%' : `${100 - rightPanelWidthPercent}%`;
    const rightFlexBasis = rightPanelWidthPercent === null ? '0%' : `${rightPanelWidthPercent}%`;


    return (
        <Form {...methods}>
            <div
                ref={containerRef}
                className="flex flex-1 h-full border rounded-lg overflow-hidden relative" // Added relative for potential absolute positioning inside
            >
                <div
                    ref={leftPanelRef}
                    className="flex flex-col h-full p-4 overflow-y-auto transition-[flex-basis] duration-100 ease-out" // Added transition
                    style={{
                        flexBasis: leftFlexBasis,
                        minWidth: `${MIN_PANEL_WIDTH_PERCENT}%`
                    }} // Set dynamic flex-basis
                >
                    <form
                        id={`playground-form-${version?.uuid ?? Math.random().toString(36).substring(7)}`}
                        onSubmit={methods.handleSubmit(onSubmit)}
                        className='flex flex-col gap-4 flex-1 h-full'
                    >
                        <div className='flex justify-between gap-4 w-full'>
                            <div className='flex items-center gap-2'>
                                <InputsDrawer
                                    open={openInputDrawer}
                                    setOpen={setOpenInputDrawer}
                                    onSubmit={onSubmit}
                                    doesProviderExist={doesProviderExist}
                                    isLoading={isRunLoading}
                                    isDisabled={isDisabled}
                                />
                                <CallParamsDrawer
                                    doesProviderExist={doesProviderExist}
                                    version={version}
                                    isLoading={isRunLoading}
                                    isDisabled={isDisabled}
                                    handleReset={handleReset}
                                />
                                {(!isCompare || showRunButton) && renderRunButton()}
                            </div>
                        </div>
                        <div className='lexical flex-1 min-h-[200px] relative'>
                            <Editor
                                inputs={inputs.map((input) => input.key)}
                                inputValues={inputValues}
                                ref={editorRef}
                                promptTemplate={version?.prompt_template ?? ""}
                                isDisabled={isDisabled}
                            />
                            {editorErrors.length > 0 &&
                                editorErrors.map((error, i) => (
                                    <div key={i} className='text-red-500 text-sm mt-1'>
                                        {error}
                                    </div>
                                ))}
                        </div>
                    </form>
                </div>

                {showRightPanel && (
                    <div
                        onMouseDown={handleMouseDown}
                        className="w-2 bg-gray-100 hover:bg-gray-200 border-x flex items-center justify-center cursor-col-resize flex-shrink-0" // Ensure handle doesn't shrink
                    >
                        <GripVertical className="h-4 w-4 text-gray-400"/>
                    </div>
                )}

                <div
                    ref={rightPanelRef}
                    className={`flex flex-col h-full p-4 overflow-y-auto transition-[flex-basis] duration-100 ease-out ${rightPanelWidthPercent === null || rightPanelWidthPercent === 0 ? 'hidden' : ''}`} // Hide if width is 0 or null
                    style={{
                        flexBasis: rightFlexBasis,
                        minWidth: showRightPanel ? `${MIN_PANEL_WIDTH_PERCENT}%` : '0%'
                    }} // Set dynamic flex-basis
                >
                    {showRightPanel && (
                        <>
                            {displayError && <PlaygroundError error={displayError}/>}
                            {!displayError && executedSpanUuid && (
                                <Suspense fallback={<CardSkeleton items={8} className='flex flex-col'/>}>
                                    <ExecutedSpanDetailPanel spanUuid={executedSpanUuid}/>
                                </Suspense>
                            )}
                        </>
                    )}
                </div>
            </div>
        </Form>
    );
};

const CallParamsDrawer = ({
  doesProviderExist,
  isLoading,
  version,
  isDisabled,
  handleReset,
}: {
  doesProviderExist: boolean;
  isLoading: boolean;
  version: FunctionPublic | null;
  isDisabled: boolean;
  handleReset: () => void;
}) => {
    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button
                    className='border border-gray-300 bg-white hover:bg-gray-100 text-gray-700'
                    variant='outline'
                    disabled={isDisabled}
                >
                    Configure Call Params
                </Button>
            </SheetTrigger>
            {/* ... SheetContent ... */}
            <SheetContent
                className='flex flex-col gap-2 overflow-y-auto'
                showOverlay={false}
            >
                <SheetHeader>
                    <SheetTitle>Call Params</SheetTitle>
                </SheetHeader>
                {!isDisabled && (
                    <div className='self-end'>
                        <SheetClose asChild>
                            <Button
                                form={`playground-form-${version?.uuid ?? Math.random().toString(36).substring(7)}`}
                                name='run'
                                type='submit'
                                loading={isLoading}
                                disabled={!doesProviderExist}
                                className='hover:bg-green-700 text-white font-medium'
                            >
                                Run
                            </Button>
                        </SheetClose>
                    </div>
                )}
                <BaseEditorFormFields isDisabled={isDisabled}/>
                <SheetFooter>
                    {!isDisabled && (
                        <Button variant='outline' onClick={handleReset}>
                            Reset to default
                        </Button>
                    )}
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
};

const InputsDrawer = ({
  open,
  setOpen,
  onSubmit,
  doesProviderExist,
  isLoading,
  isDisabled,
}: {
    open: boolean;
    setOpen: Dispatch<SetStateAction<boolean>>;
    onSubmit: SubmitHandler<EditorParameters>;
    doesProviderExist: boolean;
    isLoading: boolean;
    isDisabled: boolean;
}) => {
    const methods = useFormContext<EditorParameters>();
    const inputs = methods.watch("inputs");

    const handleClick = async (event: React.MouseEvent<HTMLButtonElement>) => {
        if (!validateInputs(methods, inputs)) {
            return;
        }
        await methods.handleSubmit((data) => onSubmit(data, event))();
        setOpen(false);
    };

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
                <Button
                    className='border border-gray-300 bg-white hover:bg-gray-100 text-gray-700'
                    variant='outline'
                    disabled={isDisabled}
                >
                    Inputs
                </Button>
            </SheetTrigger>
            <SheetContent
                className='flex flex-col sm:max-w-xl md:max-w-2xl overflow-y-auto'
                showOverlay={false}
            >
                <SheetHeader>
                    <SheetTitle>Inputs</SheetTitle>
                </SheetHeader>
                {!isDisabled && (
                    <div className='self-end'>
                        <Button
                            name='run'
                            onClick={handleClick}
                            loading={isLoading}
                            disabled={!doesProviderExist}
                            className='hover:bg-green-700 text-white font-medium'
                        >
                            Run
                        </Button>
                    </div>
                )}
                <InputsContent isDisabled={isDisabled}/>
                <SheetFooter>
                    <SheetClose asChild>
                        <Button variant='outline'>Close</Button>
                    </SheetClose>
                </SheetFooter>
            </SheetContent>
        </Sheet>
    );
};

const InputsContent = ({isDisabled}: { isDisabled: boolean }) => {
    const methods = useFormContext<EditorParameters>();
    const {fields, append, remove} = useFieldArray<EditorParameters>({
        control: methods.control,
        name: "inputs",
    });
    const types = ["str", "int", "float", "bool", "bytes", "list", "dict"];

    return (
        <div className='space-y-2'>
            <div className='flex gap-4 flex-wrap pb-4'>
                {fields.map((field, index) => {
                    const type = methods.watch(`inputs.${index}.type`);
                    return (
                        <Card key={field.id} className='w-full flex-shrink-0 relative'>
                            {/* ... Card content ... */}
                            {!isDisabled && (
                                <Button
                                    type='button'
                                    variant='ghost'
                                    size='icon'
                                    onClick={() => remove(index)}
                                    className='h-6 w-6 absolute top-2 right-2 hover:bg-gray-100'
                                >
                                    <X className='h-4 w-4'/>
                                </Button>
                            )}
                            <CardContent className='pt-6 space-y-4'>
                                <div className='w-full'>
                                    <FormField
                                        control={methods.control}
                                        name={`inputs.${index}.key`}
                                        rules={{required: 'Argument name is required'}}
                                        render={({field}) => (
                                            <FormItem>
                                                <FormLabel>Args</FormLabel>
                                                <FormControl>
                                                    <Input
                                                        placeholder='Argument Name'
                                                        disabled={isDisabled}
                                                        {...field}
                                                    />
                                                </FormControl>
                                                <FormMessage/>
                                            </FormItem>
                                        )}
                                    />
                                </div>
                                <div className='w-full flex gap-2'>
                                    <FormField
                                        control={methods.control}
                                        name={`inputs.${index}.type`}
                                        rules={{required: 'Type is required'}}
                                        render={({field}) => (
                                            <FormItem className="flex-1">
                                                <FormLabel>Type</FormLabel>
                                                {/* ... Select ... */}
                                                <FormControl>
                                                    <Select
                                                        value={field.value}
                                                        onValueChange={field.onChange}
                                                        disabled={isDisabled}
                                                    >
                                                        <SelectTrigger className='w-full'>
                                                            <SelectValue placeholder='Select input type'/>
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            {types.map((type) => (
                                                                <SelectItem key={type} value={type}>
                                                                    {type}
                                                                </SelectItem>
                                                            ))}
                                                        </SelectContent>
                                                    </Select>
                                                </FormControl>
                                                <FormMessage/>
                                            </FormItem>
                                        )}
                                    />
                                    <div className="flex-1">
                                        <TypedInput<EditorParameters>
                                            name={`inputs.${index}.value`}
                                            type={type as any}
                                        />
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
                {!isDisabled && (
                    <AddCardButton
                        className='w-full'
                        onClick={() => append({key: "", type: "str", value: ""})}
                    />
                )}
            </div>
        </div>
    );
};
