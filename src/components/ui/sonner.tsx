import { useTheme } from "next-themes"
import { Toaster as Sonner } from "sonner"

type ToasterProps = React.ComponentProps<typeof Sonner>

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      position="top-center"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-white/95 group-[.toaster]:backdrop-blur-xl group-[.toaster]:text-foreground group-[.toaster]:border-0 group-[.toaster]:shadow-2xl group-[.toaster]:rounded-2xl group-[.toaster]:py-4 group-[.toaster]:px-5",
          description: "group-[.toast]:text-muted-foreground",
          actionButton:
            "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground group-[.toast]:rounded-xl",
          cancelButton:
            "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground group-[.toast]:rounded-xl",
          success: "group-[.toaster]:bg-emerald-50/95 group-[.toaster]:text-emerald-900 group-[.toaster]:border-emerald-200/50",
          error: "group-[.toaster]:bg-rose-50/95 group-[.toaster]:text-rose-900 group-[.toaster]:border-rose-200/50",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }