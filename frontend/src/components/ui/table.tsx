"use client"

import * as React from "react"

import { cn } from "src/lib/utils"

function Table({
  className,
  ...props
}: React.ComponentProps<"table">) {
  const scrollContainerRef =
    React.useRef<HTMLDivElement | null>(null)

  const scrollRailRef =
    React.useRef<HTMLDivElement | null>(null)

  const tableRef =
    React.useRef<HTMLTableElement | null>(null)

  const [scrollWidth, setScrollWidth] =
    React.useState(0)

  const [hasHorizontalOverflow, setHasHorizontalOverflow] =
    React.useState(false)

  const [railGeometry, setRailGeometry] =
    React.useState<{
      left: number
      width: number
      visible: boolean
    }>({
      left: 0,
      width: 0,
      visible: false,
    })

  const measure = React.useCallback(() => {
    const container = scrollContainerRef.current

    if (!container) {
      return
    }

    const nextScrollWidth = container.scrollWidth
    const nextHasOverflow =
      nextScrollWidth > container.clientWidth + 1

    const rect = container.getBoundingClientRect()
    const viewportHeight = window.innerHeight
    const viewportWidth = window.innerWidth

    const verticallyVisible =
      rect.bottom > 0 &&
      rect.top < viewportHeight

    const left = Math.max(0, rect.left)
    const right = Math.min(
      viewportWidth,
      rect.right,
    )

    const width = Math.max(
      0,
      right - left,
    )

    setScrollWidth(nextScrollWidth)
    setHasHorizontalOverflow(
      nextHasOverflow,
    )

    setRailGeometry({
      left,
      width,
      visible:
        nextHasOverflow &&
        verticallyVisible &&
        width > 0,
    })

    if (!nextHasOverflow) {
      container.scrollLeft = 0

      if (scrollRailRef.current) {
        scrollRailRef.current.scrollLeft = 0
      }
    }
  }, [])

  React.useLayoutEffect(() => {
    measure()

    const container = scrollContainerRef.current
    const table = tableRef.current

    if (!container || !table) {
      return
    }

    const handleViewportChange = () => {
      measure()
    }

    window.addEventListener(
      "scroll",
      handleViewportChange,
      true,
    )

    window.addEventListener(
      "resize",
      handleViewportChange,
    )

    const resizeObserver =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(() => {
            measure()
          })
        : null

    resizeObserver?.observe(container)
    resizeObserver?.observe(table)

    return () => {
      window.removeEventListener(
        "scroll",
        handleViewportChange,
        true,
      )

      window.removeEventListener(
        "resize",
        handleViewportChange,
      )

      resizeObserver?.disconnect()
    }
  }, [measure])

  const syncFromTable = (
    event: React.UIEvent<HTMLDivElement>,
  ) => {
    const rail = scrollRailRef.current

    if (!rail) {
      return
    }

    const nextScrollLeft =
      event.currentTarget.scrollLeft

    if (
      rail.scrollLeft !== nextScrollLeft
    ) {
      rail.scrollLeft = nextScrollLeft
    }
  }

  const syncFromRail = (
    event: React.UIEvent<HTMLDivElement>,
  ) => {
    const container =
      scrollContainerRef.current

    if (!container) {
      return
    }

    const nextScrollLeft =
      event.currentTarget.scrollLeft

    if (
      container.scrollLeft !==
      nextScrollLeft
    ) {
      container.scrollLeft =
        nextScrollLeft
    }
  }

  return (
    <div
      data-slot="table-root"
      className="relative w-full min-w-0"
    >
      <div
        ref={scrollContainerRef}
        data-slot="table-container"
        className={cn(
          "relative w-full overflow-x-auto",
          "[scrollbar-width:none]",
          "[&::-webkit-scrollbar]:hidden",
        )}
        onScroll={syncFromTable}
      >
        <table
          ref={tableRef}
          data-slot="table"
          className={cn(
            "w-full caption-bottom text-sm",
            className,
          )}
          {...props}
        />
      </div>

      {hasHorizontalOverflow &&
      railGeometry.visible ? (
        <div
          data-slot="table-floating-scrollbar"
          className={cn(
            "fixed bottom-2 z-50",
            "rounded-md border",
            "bg-background/95 px-1 pt-1",
            "shadow-md backdrop-blur-sm",
          )}
          style={{
            left: railGeometry.left,
            width: railGeometry.width,
          }}
        >
          <div
            ref={scrollRailRef}
            data-slot="table-horizontal-scroll-rail"
            className={cn(
              "h-4 w-full overflow-x-auto overflow-y-hidden",
              "overscroll-x-contain",
            )}
            onScroll={syncFromRail}
            tabIndex={0}
            aria-label="Scroll table horizontally"
          >
            <div
              aria-hidden="true"
              className="h-px"
              style={{
                width: `${scrollWidth}px`,
              }}
            />
          </div>
        </div>
      ) : null}
    </div>
  )
}

function TableHeader({
  className,
  ...props
}: React.ComponentProps<"thead">) {
  return (
    <thead
      data-slot="table-header"
      className={cn(
        "[&_tr]:border-b",
        className,
      )}
      {...props}
    />
  )
}

function TableBody({
  className,
  ...props
}: React.ComponentProps<"tbody">) {
  return (
    <tbody
      data-slot="table-body"
      className={cn(
        "[&_tr:last-child]:border-0",
        className,
      )}
      {...props}
    />
  )
}

function TableFooter({
  className,
  ...props
}: React.ComponentProps<"tfoot">) {
  return (
    <tfoot
      data-slot="table-footer"
      className={cn(
        "border-t bg-muted/50 font-medium [&>tr]:last:border-b-0",
        className,
      )}
      {...props}
    />
  )
}

function TableRow({
  className,
  ...props
}: React.ComponentProps<"tr">) {
  return (
    <tr
      data-slot="table-row"
      className={cn(
        "border-b transition-colors hover:bg-muted/50 has-aria-expanded:bg-muted/50 data-[state=selected]:bg-muted",
        className,
      )}
      {...props}
    />
  )
}

function TableHead({
  className,
  ...props
}: React.ComponentProps<"th">) {
  return (
    <th
      data-slot="table-head"
      className={cn(
        "h-10 px-2 text-left align-middle font-medium whitespace-nowrap text-foreground [&:has([role=checkbox])]:pr-0",
        className,
      )}
      {...props}
    />
  )
}

function TableCell({
  className,
  ...props
}: React.ComponentProps<"td">) {
  return (
    <td
      data-slot="table-cell"
      className={cn(
        "p-2 align-middle whitespace-nowrap [&:has([role=checkbox])]:pr-0",
        className,
      )}
      {...props}
    />
  )
}

function TableCaption({
  className,
  ...props
}: React.ComponentProps<"caption">) {
  return (
    <caption
      data-slot="table-caption"
      className={cn(
        "mt-4 text-sm text-muted-foreground",
        className,
      )}
      {...props}
    />
  )
}

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
}
