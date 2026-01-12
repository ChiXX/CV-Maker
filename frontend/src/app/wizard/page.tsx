import { Wizard } from '@/components/Wizard';

export const metadata = {
  title: 'Generation - CV Maker',
  description: 'Generate your professional CV and Cover Letter with AI',
};

export default function WizardPage() {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 sm:text-4xl">
          Generate Application
        </h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400">
          Paste a job URL and let AI do the heavy lifting.
        </p>
      </div>
      <Wizard />
    </div>
  );
}
