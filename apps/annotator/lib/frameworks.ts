import type { Framework } from './types';
import demo from './gm/demo.json';
export const DEMO_TEXT = demo.map(r => r.sentence).join('\n\n');
export const BUILTIN_FRAMEWORKS: Framework[] = [{id:'halliday-gm-v3',name:'语法隐喻 · Halliday Schema v3',description:'概念与人际轴独立判断；保留一致式、映射与反证。机器建议均须审核。',version:1,builtin:true,prompt:'Use HALLIDAY_CORE. Identify semantic–lexicogrammatical remapping, never diagnose from nominalization or morphology alone. Give plausible congruent agnates, both mapping layers, counterevidence and independent ideational/interpersonal decisions. Do not invent verified sources.',nodes:[{id:'gm',label:'语法隐喻判断',color:'#236a62',children:[{id:'gm-ideational',label:'概念语法隐喻',color:'#2b7b66'},{id:'gm-interpersonal',label:'人际语法隐喻',color:'#b57536'},{id:'gm-indeterminate',label:'待定／边界实例',color:'#8878a2'},{id:'gm-non-metaphorical',label:'非语法隐喻',color:'#71828b'}]}]}];
export const DEMO_RECORDS = demo;
