// GetDP 2-D magnetostatics, vector potential a = A_z e_z, linear magnet H = nu (B - Br).
Group {
  Magnet = Region[1];
  Air = Region[2];
  Outer = Region[10];
  Domain = Region[{Magnet, Air}];
}
Function {
  mu0 = 4e-7*Pi;
  nu[Magnet] = 1/(1.05*mu0);
  nu[Air] = 1/mu0;
  br[Magnet] = Vector[1.33, 0, 0];
}
Constraint {
  { Name a_Dir; Case { { Region Outer; Value 0.; } } }
}
Jacobian {
  { Name Vol; Case { { Region All; Jacobian Vol; } } }
}
Integration {
  { Name Int; Case { { Type Gauss; Case { { GeoElement Triangle; NumberOfPoints 4; } } } } }
}
FunctionSpace {
  { Name Hcurl_a; Type Form1P;
    BasisFunction {
      { Name se; NameOfCoef ae; Function BF_PerpendicularEdge; Support Domain; Entity NodesOf[All]; }
    }
    Constraint { { NameOfCoef ae; EntityType NodesOf; NameOfConstraint a_Dir; } }
  }
}
Formulation {
  { Name MagSta_a; Type FemEquation;
    Quantity { { Name a; Type Local; NameOfSpace Hcurl_a; } }
    Equation {
      Galerkin { [ nu[] * Dof{d a}, {d a} ]; In Domain; Jacobian Vol; Integration Int; }
      Galerkin { [ -nu[] * br[], {d a} ]; In Magnet; Jacobian Vol; Integration Int; }
    }
  }
}
Resolution {
  { Name MagSta_a;
    System { { Name A; NameOfFormulation MagSta_a; } }
    Operation { Generate[A]; Solve[A]; SaveSolution[A]; }
  }
}
PostProcessing {
  { Name MagSta_a; NameOfFormulation MagSta_a;
    Quantity {
      { Name b; Value { Term { [ {d a} ]; In Domain; Jacobian Vol; } } }
    }
  }
}
PostOperation {
  { Name Get_B; NameOfPostProcessing MagSta_a;
    Operation {
      Print[ b, OnPoint {0.0, 0.0, 0}, Format Table, File "b_center.txt" ];
      Print[ b, OnPoint {0.004, 0.003, 0}, Format Table, File "b_inside.txt" ];
    }
  }
}
