import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { RocketIcon, ArrowRightIcon, PhoneCallIcon } from "lucide-react";
import { LogoCloud } from "@/components/ui/logo-cloud-3";

export function HeroSection() {
	return (
		<section className="mx-auto w-full max-w-5xl relative">
			{/* Top Shades */}
			<div
				aria-hidden="true"
				className="absolute inset-0 isolate hidden overflow-hidden contain-strict lg:block"
			>
				<div className="absolute inset-0 -top-14 isolate -z-10 bg-[radial-gradient(35%_80%_at_49%_0%,rgba(var(--primary-rgb),0.1),transparent)] contain-strict" />
			</div>

			{/* X Bold Faded Borders */}
			<div
				aria-hidden="true"
				className="absolute inset-0 mx-auto hidden min-h-screen w-full max-w-5xl lg:block"
			>
				<div className="mask-y-from-80% mask-y-to-100% absolute inset-y-0 left-0 z-10 h-full w-px bg-foreground/10" />
				<div className="mask-y-from-80% mask-y-to-100% absolute inset-y-0 right-0 z-10 h-full w-px bg-foreground/10" />
			</div>

			{/* main content */}

			<div className="relative flex flex-col items-center justify-center gap-5 pt-32 pb-30">
				{/* X Content Faded Borders */}
				<div
					aria-hidden="true"
					className="absolute inset-0 -z-10 size-full overflow-hidden"
				>
					<div className="absolute inset-y-0 left-4 w-px bg-gradient-to-b from-transparent via-border to-border md:left-8" />
					<div className="absolute inset-y-0 right-4 w-px bg-gradient-to-b from-transparent via-border to-border md:right-8" />
					<div className="absolute inset-y-0 left-8 w-px bg-gradient-to-b from-transparent via-border/50 to-border/50 md:left-12" />
					<div className="absolute inset-y-0 right-8 w-px bg-gradient-to-b from-transparent via-border/50 to-border/50 md:right-12" />
				</div>

				<a
					className={cn(
						"group mx-auto flex w-fit items-center gap-3 rounded-full border bg-card px-3 py-1 shadow",
						"animate-in fade-in slide-in-from-bottom-10 fill-mode-backwards transition-all delay-500 duration-500 ease-out"
					)}
					href="#link"
				>
					<RocketIcon className="size-3 text-muted-foreground" />
					<span className="text-xs">Shipped new AI features!</span>
					<span className="block h-5 border-l" />

					<ArrowRightIcon className="size-3 duration-150 ease-out group-hover:translate-x-1" />
				</a>

				<h1
					className={cn(
						"fade-in slide-in-from-bottom-10 animate-in text-balance fill-mode-backwards text-center text-4xl tracking-tight delay-100 duration-500 ease-out md:text-5xl lg:text-7xl",
						"text-shadow-[0_0px_50px_rgba(var(--foreground-rgb),.2)]"
					)}
				>
					Prospecting That <br /> Scales and Converts
				</h1>

				<p className="fade-in slide-in-from-bottom-10 mx-auto max-w-md animate-in fill-mode-backwards text-center text-base text-foreground/80 tracking-wider delay-200 duration-500 ease-out sm:text-lg md:text-xl">
					Discover world-class talent and <br /> automate your outreach funnel.
				</p>

				<div className="fade-in slide-in-from-bottom-10 flex animate-in flex-row flex-wrap items-center justify-center gap-3 fill-mode-backwards pt-4 delay-300 duration-500 ease-out z-20">
					<Button className="rounded-full h-12 px-6" size="lg" variant="secondary" asChild>
						<Link href="/book-demo">
							<PhoneCallIcon className="size-4 mr-2" />{" "}
							Book a Demo
						</Link>
					</Button>
					<Button className="rounded-full h-12 px-6" size="lg" asChild>
						<Link href="/create-account">
							Start Free Trial{" "}
							<ArrowRightIcon className="size-4 ms-2" />
						</Link>
					</Button>
				</div>
			</div>
		</section>
	);
}

export function LogosSection() {
	return (
		<section className="relative space-y-4 border-y py-12 bg-muted/30">
			<h2 className="text-center font-medium text-sm text-muted-foreground tracking-widest uppercase md:text-md">
				Trusted by <span className="text-foreground">innovative</span> teams
			</h2>
			<div className="relative z-10 mx-auto max-w-4xl pt-6">
				<LogoCloud logos={logos} />
			</div>
		</section>
	);
}

const logos = [
	{
		src: "https://images.unsplash.com/photo-1611162617474-5b21e879e113?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80",
		alt: "Brand 1",
	},
	{
		src: "https://images.unsplash.com/photo-1611162616305-c69b3fa7fbe0?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80",
		alt: "Brand 2",
	},
	{
		src: "https://images.unsplash.com/photo-1611162618071-b39a2ec055ce?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80",
		alt: "Brand 3",
	},
	{
		src: "https://images.unsplash.com/photo-1611162618991-886d34e803c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80",
		alt: "Brand 4",
	},
	{
		src: "https://images.unsplash.com/photo-1611162616475-46b635cb6868?ixlib=rb-4.0.3&auto=format&fit=crop&w=200&q=80",
		alt: "Brand 5",
	},
];
