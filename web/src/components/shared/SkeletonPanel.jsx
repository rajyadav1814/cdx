import { Skeleton } from '@/components/ui/skeleton'

export default function SkeletonPanel() {
  return (
    <div className="p-6 space-y-6 h-full overflow-hidden">
      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card space-y-2">
            <Skeleton className="h-3 w-16 bg-bg-surface3" />
            <Skeleton className="h-9 w-20 bg-bg-surface3" />
          </div>
        ))}
      </div>
      {/* Main content area */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 card space-y-3">
          <Skeleton className="h-3 w-24 bg-bg-surface3" />
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-10 w-full bg-bg-surface3" />
          ))}
        </div>
        <div className="card space-y-3">
          <Skeleton className="h-3 w-20 bg-bg-surface3" />
          <Skeleton className="h-40 w-full bg-bg-surface3" />
          <Skeleton className="h-3 w-full bg-bg-surface3" />
          <Skeleton className="h-3 w-4/5 bg-bg-surface3" />
          <Skeleton className="h-3 w-3/5 bg-bg-surface3" />
        </div>
      </div>
    </div>
  )
}
