import { useTheme } from "@/contexts/ThemeContext"
import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      position="top-center"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-white/95 dark:group-[.toaster]:bg-slate-800/95 group-[.toaster]:backdrop-blur-xl group-[.toaster]:text-gray-900 dark:group-[.toaster]:text-gray-100 group-[.toaster]:border-0 group-[.toaster]:shadow-2xl group-[.toaster]:rounded-2xl group-[.toaster]:py-4 group-[.toaster]:px-5",
          description: "group-[.toast]:text-gray-600 dark:group-[.toast]:text-gray-400",
          actionButton:
            "group-[.toast]:bg-blue-600 group-[.toast]:text-white group-[.toast]:rounded-xl",
          cancelButton:
            "group-[.toast]:bg-gray-200 dark:group-[.toast]:bg-slate-700 group-[.toast]:text-gray-900 dark:group-[.toast]:text-gray-100 group-[.toast]:rounded-xl",
          success: "group-[.toaster]:bg-emerald-50/95 dark:group-[.toaster]:bg-emerald-900/90 group-[.toaster]:text-emerald-900 dark:group-[.toaster]:text-emerald-100 group-[.toaster]:border-emerald-200/50 dark:group-[.toaster]:border-emerald-700/50",
          error: "group-[.toaster]:bg-rose-50/95 dark:group-[.toaster]:bg-rose-900/90 group-[.toaster]:text-rose-900 dark:group-[.toaster]:text-rose-100 group-[.toaster]:border-rose-200/50 dark:group-[.toaster]:border-rose-700/50",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }