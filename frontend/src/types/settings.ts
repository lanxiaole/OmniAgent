// settings.ts - 设置页相关类型定义

/** 场景预设 */
export interface ScenarioPreset {
  id: string;
  name: string;
  icon: string;
  description: string;
  system_prompt?: string;
  enabled_tools?: string[];
  /** 是否为系统内置场景（只读） */
  is_system?: boolean;
  /** 是否在启动页展示 */
  display?: boolean;
}

/** 场景表单（创建/编辑自定义场景用） */
export interface ScenarioForm {
  name: string;
  icon: string;
  description: string;
  system_prompt: string;
  enabled_tools: string[];
}