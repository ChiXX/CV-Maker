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
                  flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors
                  ${isCompleted
                    ? 'bg-green-500 border-green-500 text-white cursor-pointer hover:bg-green-600'
                    : isCurrent
                    ? 'border-blue-500 text-blue-500 bg-white'
                    : 'border-gray-300 text-gray-300 bg-white'
                  }
                  ${isClickable ? 'cursor-pointer hover:border-blue-400' : 'cursor-not-allowed'}
                `}
              >
                {isCompleted ? (
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <span className="text-sm font-medium">{step.id}</span>
                )}
              </button>

              {index < steps.length - 1 && (
                <div
                  className={`w-16 h-0.5 mx-2 transition-colors ${
                    step.id < currentStep ? 'bg-green-500' : 'bg-gray-300'
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
