import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { isAbnormal, vitalRanges } from '@/lib/vital-ranges';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { cn } from '@/lib/utils';

const vitalsSchema = z.object({
  heart_rate: z.coerce.number().min(0).optional(),
  respiratory_rate: z.coerce.number().min(0).optional(),
  temperature: z.coerce.number().min(20).max(45).optional(),
  oxygen_saturation: z.coerce.number().min(0).max(100).optional(),
  systolic_bp: z.coerce.number().min(0).optional(),
  diastolic_bp: z.coerce.number().min(0).optional(),
});

type VitalsFormValues = z.infer<typeof vitalsSchema>;

interface VitalsFormProps {
  initialData?: Partial<VitalsFormValues>;
  onSubmit: (data: VitalsFormValues) => void;
  onBack: () => void;
}

export function VitalsForm({ initialData, onSubmit, onBack }: VitalsFormProps) {
  const form = useForm<VitalsFormValues>({
    resolver: zodResolver(vitalsSchema),
    defaultValues: initialData || {},
  });

  const handleSubmit = (data: VitalsFormValues) => {
    if (!data.oxygen_saturation) {
      form.setError('root', { message: 'MISSING_CRITICAL_VITALS: Oxygen Saturation (SpO2) is required.' });
      return;
    }
    onSubmit(data);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {form.formState.errors.root && (
          <div className="p-3 bg-red-100 text-red-700 rounded-md border border-red-300">
            {form.formState.errors.root.message}
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(Object.keys(vitalRanges) as Array<keyof VitalsFormValues>).map((vital) => (
            <FormField
              key={vital}
              control={form.control}
              name={vital}
              render={({ field }) => {
                const isValAbnormal = field.value !== undefined && field.value !== '' && isAbnormal(vital, Number(field.value));
                return (
                  <FormItem>
                    <FormLabel className="capitalize">{vital.replace('_', ' ')} ({vitalRanges[vital].label})</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        value={field.value ?? ''}
                        className={cn(isValAbnormal && "border-red-500 bg-red-50 text-red-900")}
                      />
                    </FormControl>
                    {isValAbnormal && (
                      <p className="text-xs text-red-500 font-medium mt-1">
                        Abnormal (Normal: {vitalRanges[vital].min} - {vitalRanges[vital].max})
                      </p>
                    )}
                    <FormMessage />
                  </FormItem>
                );
              }}
            />
          ))}
        </div>
        <div className="flex justify-between">
          <Button type="button" variant="outline" onClick={onBack}>Back</Button>
          <Button type="submit">Next: Symptoms</Button>
        </div>
      </form>
    </Form>
  );
}
