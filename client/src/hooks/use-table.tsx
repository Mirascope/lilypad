import { createContext, ReactNode, useContext, useState } from "react";

// Create a generic table context
export interface TableContextType<T> {
  // Selected rows state
  selectedRows: T[];
  setSelectedRows: (rows: T[]) => void;

  // Detail panel state
  detailRow: T | null;
  setDetailRow: (row: T | null) => void;
  onDetailPanelOpen: (detailRow: T) => void;
  onDetailPanelClose: () => void;
}

// Create the context with a default value (empty context)
export const TableContext = createContext<TableContextType<any>>({
  selectedRows: [],
  setSelectedRows: () => {},
  detailRow: null,
  setDetailRow: () => {},
  onDetailPanelOpen: () => {},
  onDetailPanelClose: () => {},
});

// Custom hook to use the table context with proper typing
export function useTable<T>(): TableContextType<T> {
  return useContext(TableContext);
}

// Generic Provider component to wrap around application
export function TableProvider<T>({
  children,
  onPanelClose,
  onPanelOpen,
}: {
  children: ReactNode;
  onPanelOpen?: (detailRow: T) => void;
  onPanelClose?: () => void;
}) {
  const [selectedRows, setSelectedRowsState] = useState<T[]>([]);
  const [detailRow, setDetailRowState] = useState<T | null>(null);

  const setSelectedRows = (rows: T[]) => {
    setSelectedRowsState(rows);
  };

  const setDetailRow = (row: T | null) => {
    if (row) {
      onPanelOpen?.(row);
    }
    setDetailRowState(row);
  };

  const handleDetailPanelClose = () => {
    setDetailRowState(null);
    if (onPanelClose) {
      onPanelClose();
    }
  };

  // Create the context value with proper typing
  const contextValue: TableContextType<T> = {
    selectedRows,
    setSelectedRows,
    detailRow,
    setDetailRow,
    onDetailPanelOpen: handleDetailPanelClose,
    onDetailPanelClose: handleDetailPanelClose,
  };

  return (
    <TableContext.Provider value={contextValue}>
      {children}
    </TableContext.Provider>
  );
}
