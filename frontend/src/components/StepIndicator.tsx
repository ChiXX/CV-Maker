import { WizardStep } from '@/types';

interface StepIndicatorProps {
  steps: WizardStep[];
  currentStep: number;
  onStepClick: (step: number) => void;
}

export function StepIndicator({ steps, currentStep, onStepClick }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center">
      <div className="flex items-center space-x-4">
        {steps.map((step, index) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;
          const isClickable = step.id <= currentStep;

          return (
            <div key={step.id} className="flex items-center">
              <button
                onClick={() => isClickable && onStepClick(step.id)}
                disabled={!isClickable}
                className={`
                  flex items-center justify-center w-12 h-12 rounded-2xl border-2 transition-all duration-500
                  ${isCurrent
                    ? 'bg-zinc-900 border-zinc-900 text-white dark:bg-white dark:border-white dark:text-zinc-900 shadow-xl scale-110 z-10'
                    : isCompleted
                    ? 'bg-zinc-100 border-zinc-200 text-zinc-900 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-100'
                    : 'border-zinc-200 text-zinc-300 dark:border-zinc-800 dark:text-zinc-700 bg-transparent'
                  }
                  ${isClickable ? 'cursor-pointer hover:shadow-lg' : 'cursor-not-allowed'}
                `}
              >
                {isCompleted ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="3">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span className="text-base font-bold">{step.id}</span>
                )}
              </button>

              {index < steps.length - 1 && (
                <div
                  className={`w-12 sm:w-20 h-1 mx-2 rounded-full transition-all duration-700 ${
                    step.id < currentStep ? 'bg-zinc-900 dark:bg-white' : 'bg-zinc-200 dark:bg-zinc-800'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
