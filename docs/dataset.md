# ABC Dataset Information

## Source
- Provided by Professor Sk Aziz Ali
- Dropbox Link: [ABC Annotation Samples](https://www.dropbox.com/scl/fi/k94p4wlkt2rfp0idpxx6f/ABC_AnnotationSamples.zip?rlkey=4wniqi2bbltpradmci79xd14w&dl=0)

## Contents
The dataset includes CAD models and BRep annotations:
- `abc_v1.0_BREPEdges/`: BRep edge annotations
- `abc_v1.0_BREPJunctions/`: Junction annotations
- `abc_v1.0_BRepFaceLabels/`: Face-level labels for BRep models
- `abc_v1.0_BoundaryLabels/`: Boundary labels
- `obj/`: OBJ file versions of models
- `step/`: STEP files for BRep processing

## File Structuredata_samples/
├── abc_0001_obj_v00/
│ ├── 00010539/
│ │ ├── 00010539_919044145dd24288a1945b5c.obj
│ │ └── ...
│ └── ...
├── abc_0001_step_v00/
│ ├── 00010539/
│ │ ├── 00010539_919044145dd24288a1945b5c_step_001.step
│ │ └── ...
│ └── ...
└── ... (annotation folders)
## Usage
1. Download dataset from Dropbox link
2. Unzip into project's `data_samples/` directory
3. File paths in code reference:
   - `data_samples/abc_0001_obj_v00/` for OBJ files
   - `data_samples/abc_0001_step_v00/` for STEP files
