import { SpanPublic } from "@/types/types";
import { createContext, ReactNode, useContext, useState } from "react";

// Create a context for the selected rows
export const SelectedRowsContext = createContext<{
  rows: SpanPublic[];
  setSelectedRows: (rows: SpanPublic[]) => void;
}>({
  rows: [],
  setSelectedRows: () => {},
});

// Custom hook to use the selected rows context
export const useSelectedRows = () => useContext(SelectedRowsContext);

// Provider component to wrap around application
export const SelectedRowsProvider = ({ children }: { children: ReactNode }) => {
  const [rows, setRows] = useState<SpanPublic[]>([]);
  const setSelectedRows = (rows: SpanPublic[]) => {
    setRows(rows);
  };
  return (
    <SelectedRowsContext.Provider value={{ rows, setSelectedRows }}>
      {children}
    </SelectedRowsContext.Provider>
  );
};
