import { InfiniteSlider } from "@/components/ui/infinite-slider";
import { cn } from "@/lib/utils";

type Logo = {
  src: string;
  alt: string;
  width?: number;
  height?: number;
};

type LogoCloudProps = React.ComponentProps<"div"> & {
  logos: Logo[];
};

export function LogoCloud({ className, logos, ...props }: LogoCloudProps) {
  return (
    <div
      {...props}
      className={cn(
        "overflow-hidden py-4 mask-[linear-gradient(to_right,transparent,black,transparent)]",
        className
      )}
    >
      <InfiniteSlider gap={42} reverse duration={80} durationOnHover={25}>
        {logos.map((logo) => (
          <img
            alt={logo.alt}
            className="pointer-events-none h-10 w-auto select-none md:h-12 object-contain grayscale opacity-60 hover:grayscale-0 hover:opacity-100 transition-all dark:brightness-0 dark:invert rounded-md"
            height={logo.height || "auto"}
            key={`logo-${logo.alt}`}
            loading="lazy"
            src={logo.src}
            width={logo.width || "auto"}
          />
        ))}
      </InfiniteSlider>
    </div>
  );
}
