import type { ComponentType } from 'react';
import type { AssistantActivity, AssistantStatus } from '../../lib/assistantStatus';
import MycoAvatar from './MycoAvatar';
import ClassicAvatar from './ClassicAvatar';

export interface AvatarProps {
  activity: AssistantActivity;
  status: AssistantStatus;
}

export interface AvatarRegistryEntry {
  id: string;
  name: string;
  description: string;
  Component: ComponentType<AvatarProps>;
}

export const avatarsRegistry: AvatarRegistryEntry[] = [
  {
    id: 'myco',
    name: 'Myco Mascot',
    description: 'Dynamic vector mushroom mascot with reactive animations and assets.',
    Component: MycoAvatar,
  },
  {
    id: 'classic',
    name: 'Classic Indicators',
    description: 'Original high-contrast Lucide icon status badges with active pulses.',
    Component: ClassicAvatar,
  },
];
