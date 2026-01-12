import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-16">
      <section className="text-center space-y-6 max-w-3xl">
        <h1 className="text-5xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-100 sm:text-6xl bg-clip-text text-transparent bg-gradient-to-b from-zinc-900 to-zinc-500 dark:from-white dark:to-zinc-500">
          Your AI Career Assistant
        </h1>
        <p className="text-xl text-zinc-600 dark:text-zinc-400 leading-relaxed">
          CV Maker helps you craft the perfect application for every job. 
          Extract job details, generate tailored CVs, and write compelling cover letters in seconds.
        </p>
        <div className="flex flex-wrap justify-center gap-4 pt-4">
          <Link
            href="/wizard"
            className="px-8 py-3 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-semibold rounded-2xl shadow-xl hover:scale-105 transition-all duration-300 ring-1 ring-zinc-900/5 dark:ring-white/10"
          >
            Start New Application
          </Link>
          <Link
            href="/applications"
            className="px-8 py-3 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white font-semibold rounded-2xl shadow-lg border border-zinc-200 dark:border-zinc-800 hover:scale-105 transition-all duration-300"
          >
            View Applications
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-5xl">
        <FeatureCard 
          title="JD Extraction" 
          description="Simply paste a job URL, and we'll extract the core requirements and company info using advanced LLMs."
          icon="🌐"
        />
        <FeatureCard 
          title="AI CV Tailoring" 
          description="Get a professionally formatted LaTeX CV optimized for the specific job description."
          icon="📄"
        />
        <FeatureCard 
          title="Cover Letters" 
          description="Generate personalized cover letters that highlight your strengths and fit for the role."
          icon="✉️"
        />
      </section>
    </div>
  );
}

function FeatureCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="p-8 bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-sm hover:shadow-xl transition-all duration-500 group">
      <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">{icon}</div>
      <h3 className="text-xl font-bold mb-2 text-zinc-900 dark:text-zinc-100">{title}</h3>
      <p className="text-zinc-600 dark:text-zinc-400 leading-relaxed">
        {description}
      </p>
    </div>
  );
}
