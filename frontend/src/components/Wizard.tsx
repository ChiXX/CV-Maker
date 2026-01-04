'use client';

import { useState } from 'react';
import { WizardData, WizardStep } from '@/types';
import { StepIndicator } from './StepIndicator';
import { UrlInputStep } from './steps/UrlInputStep';
import { ExtractionStep } from './steps/ExtractionStep';
import { CvGenerationStep } from './steps/CvGenerationStep';
import { ClGenerationStep } from './steps/ClGenerationStep';

const steps: WizardStep[] = [
  { id: 1, title: 'Job URL', description: 'Paste the job posting URL' },
  { id: 2, title: 'Extract Content', description: 'Review extracted job details' },
  { id: 3, title: 'Generate CV', description: 'Create customized CV' },
  { id: 4, title: 'Generate Cover Letter', description: 'Create tailored cover letter' },
];

export function Wizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [wizardData, setWizardData] = useState<WizardData>({
    url: '',
  });

  const updateWizardData = (updates: Partial<WizardData>) => {
    setWizardData(prev => ({ ...prev, ...updates }));
  };

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (step: number) => {
    if (step >= 1 && step <= steps.length) {
      setCurrentStep(step);
    }
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <UrlInputStep
            data={wizardData}
            onUpdate={updateWizardData}
            onNext={nextStep}
          />
        );
      case 2:
        return (
          <ExtractionStep
            data={wizardData}
            onUpdate={updateWizardData}
            onNext={nextStep}
            onPrev={prevStep}
          />
        );
      case 3:
        return (
          <CvGenerationStep
            data={wizardData}
            onUpdate={updateWizardData}
            onNext={nextStep}
            onPrev={prevStep}
          />
        );
      case 4:
        return (
          <ClGenerationStep
            data={wizardData}
            onUpdate={updateWizardData}
            onNext={() => {
              // Since we removed step 5, after step 4 we should restart
              setCurrentStep(1);
              setWizardData({ url: '' });
            }}
            onPrev={prevStep}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-center text-gray-900 mb-2">
            CV Maker
          </h1>
          <p className="text-center text-gray-600">
            Generate customized CV and cover letters from job postings
          </p>
        </div>

        <StepIndicator steps={steps} currentStep={currentStep} onStepClick={goToStep} />

        <div className="mt-8">
          {renderCurrentStep()}
        </div>
      </div>
    </div>
  );
}
